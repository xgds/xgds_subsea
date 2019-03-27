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
from django.conf import settings

from redis_utils import TelemetrySaver, ensure_vehicle, patch_yaml_path

from eventLogcsvImporter import EventLogCsvImporter

BROADCAST = settings.XGDS_CORE_REDIS and settings.XGDS_SSE  # type: bool


class EventSaver(TelemetrySaver):
    def __init__(self, options):
        # Create an EventLogCsvImporter object with no corresponding CSV file:
        ensure_vehicle(options)
        patch_yaml_path(options)

        self.importer = EventLogCsvImporter(options['config_yaml'], None,
                                    options['vehicle'])
                                    #options['timezone'],
                                    #options['input'],
                                    #options['reload'],
                                    #options['replace'],
                                    #options['skip_bad'])
        self.delimiter = self.importer.config['delimiter']
        super(EventSaver, self).__init__(options)

    def deserialize(self, msg):
        """
        In this case the deserialize also stores the models
        :param msg:
        :return:
        """
        try:
            values = msg.split(self.delimiter)
            row = {k: v for k, v in zip(self.keys, values)}
            row = self.importer.update_row(row)
            models = self.importer.build_models(row, BROADCAST)
            return None  # because the importer build models stores them
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
            savers.append(EventSaver(params))
        while True:
            sleep(1)
