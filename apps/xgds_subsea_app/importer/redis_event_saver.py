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

import yaml
import traceback
from time import sleep
from redis_utils import TelemetrySaver

import django
django.setup()
from eventLogcsvImporter import EventLogCsvImporter

from geocamUtil.loader import getModelByName


class EventSaver(TelemetrySaver):
    def __init__(self, options):
        # Create an EventLogCsvImporter object with no corresponding CSV file:
        self.lookup_flight(options)
        self.importer = EventLogCsvImporter(options['config_yaml'], None,
                                    options['vehicle'],
                                    options['flight']) #,
                                    #options['timezone'],
                                    #options['input'],
                                    #options['reload'],
                                    #options['replace'],
                                    #options['skip_bad'])
        self.keys = self.importer.config['fields'].keys()
        self.delimiter = self.importer.config['delimiter']
        self.model = getModelByName(self.importer.config['class'])
        super(EventLogCsvImporter, self).__init__(options)

    def deserialize(self, msg):
        try:
            values = msg.split(self.delimiter)
            row = {k: v for k, v in zip(self.keys, values)}
            row = self.importer.update_row(row)
            return self.model(**row)
        except Exception as e:
            print 'deserializing:', msg
            print 'deserialized:', row
            traceback.print_exc()
            print e
            return None


if __name__=='__main__':
    with open('redis_csv_saver_config.yaml', 'r') as fp:
        config = yaml.load(fp)

    verbose = False
    if 'verbose' in config:
        verbose = config['verbose']

    if 'savers' in config:
        savers = []
        for name, params in config['savers'].iteritems():
            savers.append(EventSaver(params))
        while True:
            sleep(1)
