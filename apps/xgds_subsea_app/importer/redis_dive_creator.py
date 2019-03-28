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
import traceback
from time import sleep
from dateutil.parser import parse as dateparse

import django

django.setup()
from django.conf import settings

from xgds_core.flightUtils import getFlight, getActiveFlight, create_group_flight, end_group_flight
from redis_utils import TelemetryQueue
from geocamTrack.utils import LazyGetModelByName
from eventLogcsvImporter import EventLogCsvImporter

VEHICLE_MODEL = LazyGetModelByName(settings.XGDS_CORE_VEHICLE_MODEL)
GROUP_FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_GROUP_FLIGHT_MODEL)
FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_FLIGHT_MODEL)
ACTIVE_FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_CORE_ACTIVE_FLIGHT_MODEL)

# This script should do the following:
# Listen to events
# If we get an inwater event, create a flight and set it active
# If we get an ondeck event, end the flight


class DiveCreator(object):
    def __init__(self,config):
        self.verbose = config['verbose']

        # All of the vehicles that will make up a group flight
        self.vehicles = VEHICLE_MODEL.get().objects.all()

        # Is there a current active group flight?
        active_flight = getActiveFlight()
        if active_flight is not None:
            # there's an active flight underway
            self.active_dive = active_flight.group

        self.importer = EventLogCsvImporter(config['config_yaml'], None, None)
        self.delimiter = self.importer.config['delimiter']
        self.keys = self.importer.config['fields'].keys()
        self.tq = TelemetryQueue(config['channel_name'])

        # Start listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def get_last_flight_number(self):
        last_name = GROUP_FLIGHT_MODEL.get().objects.all().order_by('-name')[0].name
        number = int(last_name[1:])
        return number

    def start_dive(self, group_flight_name):
        # call create_group_flight
        self.active_dive = create_group_flight(group_flight_name, notes=None, vehicles=self.vehicles)

    def end_dive(self):
        group_flight_name = self.active_dive.name
        end_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        end_group_flight(group_flight_name, end_time)
        self.active_dive = None

    def run(self):
        for msg in self.tq.listen():
            print msg['data']
            try:
                values = msg['data'].split(self.delimiter)
                row = {k: v for k, v in zip(self.keys, values)}
                row = self.importer.update_row(row)
            except Exception as e:
                print 'deserializing:', msg
                print 'deserialized:', row
                traceback.print_exc()
                print e
                return None

            print row
            if 'DIVESTATUSEVENT' in row and row['DIVESTATUSEVENT'] == 'inwater':
                if self.active_dive is None:
                    # Try to get the group flight name from the event message
                    group_flight_name = None
                    if 'DIVENUMBER' in row:
                        group_flight_name = row['DIVENUMBER']
                    else:
                        last_flight_number = self.get_last_flight_number()
                        flight_number = last_flight_number + 1
                        group_flight_name = 'H%d' % flight_number
                    self.start_dive(group_flight_name)

                if 'DIVESTATUSEVENT' == key and 'ondeck' == value:
                    self.end_dive()


if __name__ == '__main__':
    with open('redis_dive_creator_config.yaml', 'r') as fp:
        config = yaml.load(fp)

    dc = DiveCreator(config)

    while True:
        sleep(1)
