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
import argparse
import yaml
import pytz
import datetime
import threading
from time import sleep

import django

django.setup()
from django.conf import settings

from xgds_core.flightUtils import getFlight, getActiveFlight, create_group_flight, end_group_flight
from redis_utils import TelemetryQueue
from geocamTrack.utils import LazyGetModelByName

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

        self.delimiter = self.importer.config['delimiter']
        self.tq = TelemetryQueue(config['channel_name'])

        # Start listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def start_dive(self, group_flight_name):
        # call create_group_flight
        print('starting dive %s' % group_flight_name)
        self.active_dive = create_group_flight(group_flight_name, notes=None, vehicles=self.vehicles, active=True)

    def end_dive(self):
        group_flight_name = self.active_dive.name
        end_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        print('ending dive %s %s' % (group_flight_name, end_time))

        end_group_flight(group_flight_name, end_time)
        self.active_dive = None

    def run(self):
        for msg in self.tq.listen():
            data = msg['data']
            print data
            if self.active_dive:
                print 'ADIVE'
            if self.active_dive is None:
                if 'DIVESTATUSEVENT:inwater' in data:
                    # Try to get the group flight name from the event message
                    group_flight_name = None
                    if 'DIVENUMBER' in data:
                        values = data.split(self.delimiter)
                        for v in values:
                            if v.startswith('DIVENUMBER'):
                                group_flight_name = self.prefix + v.split(':')[1]
                                break
                    else:
                        last_flight_number = self.get_last_flight_number()
                        flight_number = last_flight_number + 1
                        group_flight_name = '%sH%d' % (self.prefix, flight_number)
                    self.start_dive(group_flight_name)

            else:
                if 'DIVESTATUSEVENT:ondeck' in data:
                    print 'END MATCH'
                    self.end_dive()


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
