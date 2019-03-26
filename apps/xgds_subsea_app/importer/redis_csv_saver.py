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
import traceback
from time import sleep

import django
django.setup()

from redis_utils import TelemetrySaver, lookup_active_flight
from xgds_core.importer.csvImporter import CsvImporter

from geocamUtil.loader import getModelByName


class CsvSaver(TelemetrySaver):
    def __init__(self, options):
        # look up the flight we want to use
        lookup_active_flight(options)

        # Create a CsvImporter object with no corresponding CSV file:
        self.importer = CsvImporter(options['config_yaml'], None,
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
        super(CsvSaver, self).__init__(options)

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
            savers.append(CsvSaver(params))
        while True:
            sleep(1)
