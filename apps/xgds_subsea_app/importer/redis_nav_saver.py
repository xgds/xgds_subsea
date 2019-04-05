#!/usr/bin/env python
#  __BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
# __END_LICENSE__

import traceback
import sys
import yaml
import pytz
import redis
import heapq
import bisect
import pynmea2
import datetime
import threading
from time import sleep
from dateutil.parser import parse as dateparse

import django

django.setup()
from django.conf import settings

from django.db import connection, OperationalError

from xgds_core.models import Vehicle
from xgds_core.util import persist_error
from xgds_core.flightUtils import getActiveFlight
from geocamTrack.models import ResourcePoseDepth, PastResourcePoseDepth
from redis_utils import TelemetrySaver, TelemetryQueue


def get_active_track(vehicle):
    """
    Get the active track for a vehicle
    :param vehicle: the vehicle
    :return: the track or None
    """
    flight = getActiveFlight(vehicle=vehicle)
    if flight:
        return flight.track
    return None


def interpolate(t, t1, value1, t2, value2, unwrap=False):
    if value1 is None or value2 is None:
        return None
    a = (t - t1).total_seconds() / (t2 - t1).total_seconds()
    if unwrap:
        diff = value2 - value1
        if diff > 180:
            diff -= 360
        if diff < -180:
            diff += 360
        return (value1 + a * diff) % 360
    else:
        return value1 + a * (value2 - value1)


class TimestampedItemQueue(object):
    def __init__(self):
        self.queue = []

    def append(self, timestamp, item):
        heapq.heappush(self.queue, (timestamp, item))

    def get_closest_before(self, timestamp):
        idx = bisect.bisect(self.queue, (timestamp, None))
        if 0 == idx:
            # throw an exception? this shouldn't happen given how we plan to use this
            return None
        (ts, item) = self.queue[idx - 1]
        return item

    def get_closest_after(self, timestamp):
        idx = bisect.bisect(self.queue, (timestamp, None))
        if idx > len(self.queue):
            return None
        (ts, item) = self.queue[idx]
        return item

    def delete_before(self, timestamp):
        while len(self.queue) > 1 and self.queue[0][0] < timestamp:
            heapq.heappop(self.queue)


class NavSaver(TelemetrySaver):
    def __init__(self, options):
        # Get vehicle
        if 'vehicle' not in options:
            raise ValueError('Vehicle not specified')
        self.vehicle = Vehicle.objects.get(name=options['vehicle'])

        # Get flight using current time
        # t = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        # self.flight = getFlight(t, self.vehicle)

        # Set the desired time once telemetry starts coming in
        self.current_position = None
        self.desired_pose_time = None
        self.latlon_queue = TimestampedItemQueue()
        self.rypad_queue = TimestampedItemQueue()
        super(NavSaver, self).__init__(options)

    def interpolate(self):
        # Interpolate a pose for the current desired_pose_time and return it
        prev_latlon = self.latlon_queue.get_closest_before(self.desired_pose_time)
        next_latlon = self.latlon_queue.get_closest_after(self.desired_pose_time)
        if prev_latlon is None or next_latlon is None:
            return None
        t = self.desired_pose_time
        t1 = prev_latlon['timestamp']
        t2 = next_latlon['timestamp']
        params = {'timestamp': t}
        for k in ['longitude', 'latitude']:
            params[k] = interpolate(t, t1, prev_latlon[k], t2, next_latlon[k])

        prev_rypad = self.rypad_queue.get_closest_before(self.desired_pose_time)
        next_rypad = self.rypad_queue.get_closest_after(self.desired_pose_time)
        if prev_rypad is None or next_rypad is None:
            return None
        t1 = prev_rypad['timestamp']
        t2 = next_rypad['timestamp']
        for k in ['altitude', 'depth']:
            if k in prev_rypad and k in next_rypad:
                params[k] = interpolate(t, t1, prev_rypad[k], t2, next_rypad[k])

        for k in ['roll', 'pitch', 'yaw']:
            if k in prev_rypad and k in next_rypad:
                params[k] = interpolate(t, t1, prev_rypad[k], t2, next_rypad[k], unwrap=True)

        desired_pose = None
        current_pose = None
        try:
            params['track'] = get_active_track(self.vehicle)
            desired_pose = PastResourcePoseDepth(**params)
            current_pose = ResourcePoseDepth(**params)
        except OperationalError:
            print 'Lost db connection, retrying'
            # reset db connection
            connection.close()
            connection.connect()
            params['track'] = get_active_track(self.vehicle)
            desired_pose = PastResourcePoseDepth(**params)
            current_pose = ResourcePoseDepth(**params)
        except Exception as e:
            persist_error(e)
            traceback.print_exc()

        return desired_pose, current_pose

    def deserialize(self, msg):
        """

        :param msg:
        :return: In this case we are returning a tuple, positions, current_position
        """
        #
        # TODO: This would be more efficient if it only deserialized the OET messages
        # that it needs instead of deserializing every message in case it is needed.

        # OET messages have Type, Timestamp, Source, Payload fields separated by <tab>
        # Then the payload could be a string of delimited values or a NMEA string
        parts = msg.split('\t')

        # OET message timestamp
        timestamp = dateparse(parts[1])

        # On the first time through need to set set up the time to interpolate
        # It should be the first integer second timestamp after the first timestamp we get
        if self.desired_pose_time is None:
            self.desired_pose_time = timestamp
            self.desired_pose_time = self.desired_pose_time.replace(microsecond=0)
            self.desired_pose_time += datetime.timedelta(seconds=1)

        if '$' == parts[3][0]:
            # NMEA string, should be either GGA or HDG
            nmea = pynmea2.parse(parts[3])
            if nmea.sentence_type == 'GGA':
                # GPS position fix
                latlon = {'timestamp': timestamp,
                       'longitude': nmea.longitude,
                       'latitude': nmea.latitude}
                self.latlon_queue.append(timestamp, latlon)
            elif nmea.sentence_type == 'HDG':
                # heading fix
                rypad = {'timestamp': timestamp,
                       'yaw': float(nmea.heading),
                       'pitch': None,
                       'roll': None}
                self.rypad_queue.append(timestamp, rypad)
            else:
                # not an NMEA string we need
                return None

        elif 'APAS' in parts[3]:
            # Parse timestamp, orientation, depth, and altitude from the APAS string
            # Per Justin:
            # Argus APAS string: "APAS" <date> <time> <vehicle> <heading> <pitch> <roll> <altitude> <depth>
            subparts = parts[3].split()
            timestamp = dateparse('%sT%sZ' % (subparts[1], subparts[2]))
            rypad = {'timestamp': timestamp,
                   'roll': float(subparts[6]),
                   'pitch': float(subparts[5]),
                   'yaw': float(subparts[4]),
                   'altitude': float(subparts[7]),
                   'depth': float(subparts[8])}
            self.rypad_queue.append(timestamp, rypad)

        elif 'JDS' in parts[3]:
            # Parse timestamp, orientation, depth, and altitude from the JDS string
            # Per Justin:
            # JDS lines contain: "JDS" <date> <time> <vehicle> <bad-lat> <bad-lon> <bad-easting> <bad-northing>
            # <roll> <pitch> <heading> <depth> <altitude> <elapsed_time> <tether_wraps>
            subparts = parts[3].split()
            timestamp = dateparse('%sT%sZ' % (subparts[1], subparts[2]))
            rypad = {'timestamp': timestamp,
                   'roll': float(subparts[8]),
                   'pitch': float(subparts[9]),
                   'yaw': float(subparts[10]),
                   'altitude': float(subparts[12]),
                   'depth': float(subparts[11])}
            self.rypad_queue.append(timestamp, rypad)

        else:
            print 'Unknown message:', msg
            return None

        # Get interpolated values if we can
        if len(self.rypad_queue.queue) > 1 and len(self.latlon_queue.queue) > 1:
            past_results = []
            current_results = []
            while self.rypad_queue.queue[-1][0] > self.desired_pose_time \
                    and self.latlon_queue.queue[-1][0] > self.desired_pose_time:
                # We should have the information we need to interpolate
                interpolated = self.interpolate()
                if interpolated:
                    past_pos, current_pos = interpolated
                    if past_pos is not None:
                        past_results.append(past_pos)
                    if current_pos is not None:
                        current_results.append(current_pos)
                # Increment the next desired pose time
                self.desired_pose_time += datetime.timedelta(seconds=1)

            # Get rid of older values we won't need again
            done_with = self.desired_pose_time - datetime.timedelta(seconds=1)
            self.latlon_queue.delete_before(done_with)
            self.rypad_queue.delete_before(done_with)
            if len(past_results) > 0:
                for pose in past_results:
                    print '%s pose at %s computed' % (self.vehicle, pose.timestamp)
                return past_results, current_results[-1]
        return None

    def handle_msg(self, msg):
        deserialized = self.deserialize(msg)
        if deserialized:
            past_positions, self.current_position = deserialized
        else:
            return

        if self.current_position:
            print 'saving current position from %s' % self.channel_name
            print 'current position type %s' % self.current_position.__class__.__name__
            self.current_position.saveCurrent()

        # The result should be None, a model object, or a list of model objects
        if past_positions is not None:
            if type(past_positions) is list:
                if past_positions:
                    self.buffer.extend(past_positions)
            else:
                self.buffer.append(past_positions)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "You must pass yaml file path as the first argument"
        exit(1)

    yaml_file = sys.argv[1]
    with open(yaml_file, 'r') as fp:
        config = yaml.load(fp)

    verbose = False
    if 'verbose' in config:
        verbose = config['verbose']

    if 'savers' in config:
        savers = []
        for name, params in config['savers'].iteritems():
            savers.append(NavSaver(params))
        while True:
            sleep(1)
