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
from django.db import OperationalError

from redis_utils import TelemetrySaver, ensure_vehicle, patch_yaml_path, reconnect_db
from xgds_core.util import persist_error
from xgds_core.importer.csvImporter import CsvImporter
from xgds_core.flightUtils import getActiveFlight
from geocamUtil.loader import getModelByName


class CsvSaver(TelemetrySaver):
    def __init__(self, options):

        ensure_vehicle(options)
        patch_yaml_path(options)

        # Create a CsvImporter object with no corresponding CSV file:
        self.importer = self.construct_importer(options)
        self.keys = self.importer.config['fields'].keys()
        self.delimiter = self.importer.config['delimiter']
        self.model = getModelByName(self.importer.config['class'])
        if 'verbose' in options:
            self.verbose = options['verbose']
        else:
            self.verbose = False
        self.needs_flight = False
        if hasattr(self.model(), 'flight'):
            self.needs_flight = True
        super(CsvSaver, self).__init__(options)

    def construct_importer(self, options):
        return CsvImporter(options['config_yaml'], None,
                           options['vehicle'])

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
                result = self.model(**row)
                if self.verbose:
                    print result
                return result
            except OperationalError as oe:
                reconnect_db()
                if not updated_row:
                    row = self.importer.update_row(row)
                    if self.needs_flight:
                        flight = getActiveFlight()
                        row['flight'] = flight
                    result = self.model(**row)
                    if self.verbose:
                        print result
                    return result
        except Exception as e:
            print 'deserializing:', msg
            if row:
                print 'deserialized:', row
            traceback.print_exc()
            persist_error(e)
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
            savers.append(CsvSaver(params))
        while True:
            sleep(1)
