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
import datetime
import traceback
from time import sleep

import django
django.setup()
from django.db import OperationalError

from redis_utils import TimestampedItemQueue, reconnect_db, interpolate
from redis_csv_saver import CsvSaver
from xgds_core.util import persist_error
from xgds_core.importer.csvImporter import CsvImporter
from xgds_core.flightUtils import getActiveFlight
from geocamUtil.loader import getModelByName

class CsvResampleSaver(CsvSaver):
    def __init__(self, options):
        self.resample_interval_sec = options['resample_interval_sec']
        self.desired_sample_time = None
        self.queue = TimestampedItemQueue()
        super(CsvResampleSaver, self).__init__(options)

    def interpolate(self):
        # Interpolate values for the current desired_sample_time and return it
        prev_value = self.queue.get_closest_before(self.desired_sample_time)
        post_value = self.queue.get_closest_after(self.desired_sample_time)
        if prev_value is None or post_value is None:
            return None
        t = self.desired_sample_time
        t1 = prev_value['timestamp']
        t2 = post_value['timestamp']
        print 'Interpolating between:'
        print '\t', prev_value
        print '\t', post_value

        # Interpolated values
        values = {}
        for field in prev_value.keys():
            if not datetime is type(prev_value[field]):
                values[field] = interpolate(t, t1, prev_value[field], t2, post_value[field])

        return values


    def deserialize(self, msg):
        row = None
        updated_row = False
        try:
            try:
                values = msg.split(self.delimiter)
                row = {k: v for k, v in zip(self.keys, values)}
                row = self.importer.update_row(row)
                if self.needs_flight:
                    flight = getActiveFlight()
                    row['flight'] = flight
                if self.verbose:
                    print 'deserialized', row
                self.queue.append(row['timestamp'], row)
            except OperationalError as oe:
                reconnect_db()
                if not updated_row:
                    row = self.importer.update_row(row)
                    if self.needs_flight:
                        flight = getActiveFlight()
                        row['flight'] = flight
                    if self.verbose:
                        print 'deserialized', row
                    self.queue.append(row['timestamp'], row)

            # On the first time through we need to set set up the first desired time to interpolate
            # It should be the first whole interval timestamp after the first timestamp we get
            if self.desired_sample_time is None:
                self.desired_sample_time = row['timestamp']
                desired_second = int(1 + self.desired_sample_time.second / self.resample_interval_sec) * \
                                 self.resample_interval_sec
                self.desired_sample_time = self.desired_sample_time.replace(second=desired_second)
                self.desired_sample_time = self.desired_sample_time.replace(microsecond=0)
                if self.verbose:
                    print 'resample interval is', self.resample_interval_sec
                    print 'first desired sample time is', self.desired_sample_time

            # Get interpolated values if we can
            if len(self.queue.queue) > 1:
                models = []
                while self.queue.queue[-1][0] > self.desired_sample_time:
                    # We should have the information we need to interpolate
                    values = self.interpolate()
                    if values:
                        print 'interpolated', values
                        models.append(self.model(**values))

                    # Get rid of queued data we won't need again
                    self.queue.delete_before(self.desired_sample_time)
                    # Increment the next desired pose time
                    self.desired_sample_time += datetime.timedelta(seconds=self.resample_interval_sec)
                return models
            return None

        except Exception as e:
            print 'deserializing:', msg
            if row:
                print 'deserialized:', row
            traceback.print_exc()
            persist_error(e, traceback.format_exc())
            return None


if __name__=='__main__':
    if len(sys.argv) < 2:
        print "You must pass yaml file path as the first argument"
        exit(1)

    yaml_file = sys.argv[1]
    with open(yaml_file, 'r') as fp:
        config = yaml.load(fp)

    if 'savers' in config:
        savers = []
        for name, params in config['savers'].iteritems():
            savers.append(CsvResampleSaver(params))
        while True:
            sleep(1)
