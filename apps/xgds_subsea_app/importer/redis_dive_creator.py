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

from threading import Timer
import argparse
import yaml
import pytz
import threading
from time import sleep
from dateutil.parser import parse as dateparser

import django
django.setup()
from django.conf import settings
from django.db import connection

from xgds_core.flightUtils import getFlight, getActiveFlight, create_group_flight, end_group_flight
from redis_utils import TelemetryQueue
from geocamUtil.loader import LazyGetModelByName
from geocamTrack.utils import get_or_create_track

VEHICLE_MODEL = LazyGetModelByName(settings.XGDS_CORE_VEHICLE_MODEL)
GROUP_FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_GROUP_FLIGHT_MODEL)
FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_FLIGHT_MODEL)
ACTIVE_FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_ACTIVE_FLIGHT_MODEL)

# This script should do the following:
# Listen to events
# If we get an inwater event, create a flight and set it active
# If we get an ondeck event, end the flight


def get_last_flight_number():
    last_name = GROUP_FLIGHT_MODEL.get().objects.all().order_by('-name')[0].name
    number = int(last_name[-4:])
    return number


class DiveCreator(object):
    def __init__(self, config, prefix=""):
        self.verbose = config['verbose']
        self.prefix = prefix

        # Is there a current active group flight?
        self.active_dive = None
        active_flight = getActiveFlight()
        if active_flight is not None:
            # there's an active flight underway
            self.active_dive = active_flight.group
            print 'found active dive %s ' % self.active_dive.name

        if not self.active_dive:
            print 'NO ACTIVE DIVE'

        self.delimiter = '\t'
        self.tq = TelemetryQueue(config['channel_name'])

        # Start listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def start_dive(self, group_flight_name, start_time):
        # call create_group_flight
        print('starting dive %s' % group_flight_name)
        extras = {"cruise": settings.CRUISE_ID,
                  "dive": group_flight_name,
                  "inwatertime": start_time.isoformat()}
        print extras
        self.active_dive = create_group_flight(group_flight_name, notes=None, active=True, start_time=start_time,
                                               extras=extras)

        for flight in self.active_dive.flights:
            # create a track for each flight
            track = get_or_create_track(flight.name, flight.vehicle, flight)
        print('started dive %s' % group_flight_name)

    def end_dive(self, end_time=None):
        """
        End a dive, stopping active flights and clearing self.active_dive
        :param end_time: the end time to set on all the flights
        """
        group_flight_name = self.active_dive.name
        print('ending dive %s %s' % (group_flight_name, end_time))

        # delay so other things have time to finish
        t = Timer(30, end_group_flight, [group_flight_name, end_time])
        t.start()

        self.active_dive = None

    def end_other_dive(self, group_flight_name, end_time):
        """
        End a dive that is not our active dive
        :param group_flight_name: the group flight name to look for
        :param end_time: the end time
        """
        print('ending dive %s %s' % (group_flight_name, end_time))
        end_group_flight(group_flight_name, end_time)

    def parse_data(self, data):
        """
        Gets the group flight name and the dive number and the time from the data
        :param data:
        :return: dictionary with group flight name, dive number and time
        """
        dive_number = None
        group_flight_name = None
        values = data.split(self.delimiter)

        if 'DIVENUMBER' in data:
            # Try to get the group flight name from the event message
            for v in values:
                if v.startswith('DIVENUMBER'):
                    dive_number = v.split(':')[1]
                    group_flight_name = self.prefix + dive_number
                    break
            if not group_flight_name:
                # should never happen but just in case
                last_flight_number = self.get_last_flight_number()
                flight_number = last_flight_number + 1
                group_flight_name = '%sH%d' % (self.prefix, flight_number)

        # get the time
        value = values[1]
        the_time = dateparser(value)
        the_time.replace(tzinfo=pytz.UTC)

        result = {'group_flight_name': group_flight_name,
                  'dive_number': dive_number,
                  'time': the_time}
        print result
        return result

    def run(self):
        for msg in self.tq.listen():
            data = msg['data']
            print data

            if 'DIVESTATUSEVENT:inwater' in data:
                connection.close()
                connection.connect()
                parsed_data = self.parse_data(data)
                if self.active_dive:
                    if parsed_data['dive_number']:
                        if parsed_data['dive_number'] not in self.active_dive.name:
                            # end that dive with no end time, the names do not match
                            self.end_dive()
                        else:
                            return

                # make the dive and start it
                self.start_dive(parsed_data['group_flight_name'], parsed_data['time'])

            elif 'DIVESTATUSEVENT:ondeck' in data:
                connection.close()
                connection.connect()
                parsed_data = self.parse_data(data)
                end_time = None

                if self.active_dive:
                    if parsed_data['dive_number']:
                        if parsed_data['dive_number'] in self.active_dive.name:
                            end_time = parsed_data['time']
                    self.end_dive(end_time)
                else:
                    # no active dive, but we got an end so let's end that dive
                    self.end_other_dive(parsed_data['dive_number'], parsed_data['time'])


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', type=str, help="The yaml configuration file")
    parser.add_argument('-p', '--prefix', help='prefix for group flight name', default="")
    args, unknown = parser.parse_known_args()

    # if len(sys.argv) < 2:
    #     print "You must pass yaml file path as the first argument"
    #     exit(1)
    #
    # yaml_file = sys.argv[1]
    with open(args.yaml_file, 'r') as fp:
        config = yaml.load(fp)

    dc = DiveCreator(config, args.prefix)

    while True:
        sleep(1)
