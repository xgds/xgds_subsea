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

from xgds_core.models import Vehicle
from xgds_core.flightUtils import getFlight
from geocamTrack.models import PastResourcePoseDepth
from redis_utils import TelemetrySaver


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
        vehicle = Vehicle.objects.get(name=options['vehicle'])

        # Get flight using current time
        t = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        self.flight = getFlight(t, vehicle)

        # Set the desired time once telemetry starts coming in
        self.desired_pose_time = None
        self.gps_queue = TimestampedItemQueue()
        self.nav_queue = TimestampedItemQueue()
        super(NavSaver, self).__init__(options)

    def interpolate(self):
        # Interpolate a pose for the current desired_pose_time and return it
        prev_gps = self.gps_queue.get_closest_before(self.desired_pose_time)
        next_gps = self.gps_queue.get_closest_after(self.desired_pose_time)
        if prev_gps is None or next_gps is None:
            return None
        t = self.desired_pose_time
        t1 = prev_gps['timestamp']
        t2 = next_gps['timestamp']
        params = {'timestamp': t}
        for k in ['longitude', 'latitude']:
            params[k] = interpolate(t, t1, prev_gps[k], t2, next_gps[k])

        prev_nav = self.gps_queue.get_closest_before(self.desired_pose_time)
        next_nav = self.gps_queue.get_closest_after(self.desired_pose_time)
        if prev_nav is None or next_nav is None:
            return None
        t1 = prev_nav['timestamp']
        t2 = next_nav['timestamp']
        for k in ['altitude', 'depth']:
            if k in prev_nav and k in next_nav:
                params[k] = interpolate(t, t1, prev_nav[k], t2, next_nav[k])

        for k in ['roll', 'pitch', 'yaw']:
            if k in prev_nav and k in next_nav:
                params[k] = interpolate(t, t1, prev_nav[k], t2, next_nav[k], unwrap=True)

        # TODO: a pose has a track_id, not a vehicle and flight
        # params['vehicle'] = self.vehicle
        # params['flight'] = getFlight(t,self.vehicle)
        desired_pose = PastResourcePoseDepth(**params)
        return desired_pose

    def deserialize(self, msg):
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
                gps = {'timestamp': timestamp,
                       'longitude': nmea.longitude,
                       'latitude': nmea.latitude}
                self.gps_queue.append(timestamp, gps)
            elif nmea.sentence_type == 'HDG':
                # heading fix
                nav = {'timestamp': timestamp,
                       'yaw': float(nmea.heading),
                       'pitch': None,
                       'roll': None}
                self.nav_queue.append(timestamp, nav)
            else:
                # not an NMEA string we need
                return None

        elif 'APAS' in parts[3]:
            # Parse timestamp, orientation, depth, and altitude from the APAS string
            # Per Justin:
            # Argus APAS string: "APAS" <date> <time> <vehicle> <heading> <pitch> <roll> <altitude> <depth>
            subparts = parts[3].split()
            timestamp = dateparse('%sT%sZ' % (subparts[1], subparts[2]))
            nav = {'timestamp': timestamp,
                   'roll': float(subparts[6]),
                   'pitch': float(subparts[5]),
                   'yaw': float(subparts[4]),
                   'altitude': float(subparts[7]),
                   'depth': float(subparts[8])}
            self.nav_queue.append(timestamp, nav)

        elif 'JDS' in parts[3]:
            # Parse timestamp, orientation, depth, and altitude from the JDS string
            # Per Justin:
            # JDS lines contain: "JDS" <date> <time> <vehicle> <bad-lat> <bad-lon> <bad-easting> <bad-northing>
            # <roll> <pitch> <heading> <depth> <altitude> <elapsed_time> <tether_wraps>
            subparts = parts[3].split()
            timestamp = dateparse('%sT%sZ' % (subparts[1], subparts[2]))
            nav = {'timestamp': timestamp,
                   'roll': float(subparts[8]),
                   'pitch': float(subparts[9]),
                   'yaw': float(subparts[10]),
                   'altitude': float(subparts[12]),
                   'depth': float(subparts[11])}
            self.nav_queue.append(timestamp, nav)

        else:
            print 'Unknown message:', msg
            return None

        # Get interpolated values if we can
        if len(self.nav_queue.queue) > 1 and len(self.gps_queue.queue) > 1:
            results = []
            while self.nav_queue.queue[-1][0] > self.desired_pose_time \
                    and self.gps_queue.queue[-1][0] > self.desired_pose_time:
                # We should have the information we need to interpolate
                pos = self.interpolate()
                if pos is not None:
                    results.append(pos)
                # Increment the next desired pose time
                self.desired_pose_time += datetime.timedelta(seconds=1)

            # Get rid of older values we won't need again
            done_with = self.desired_pose_time - datetime.timedelta(seconds=1)
            self.gps_queue.delete_before(done_with)
            self.nav_queue.delete_before(done_with)
            if len(results) > 0:
                for pose in results:
                    print '%s pose at %s computed' % (self.vehicle, pose.timestamp)
                return results
        return None


if __name__ == '__main__':
    with open('redis_nav_saver_config.yaml', 'r') as fp:
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