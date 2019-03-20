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
from time import sleep

import django
django.setup()
from redis_utils import TelemetrySaver, lookup_active_flight
from redis_csv_saver import CsvSaver
from sciChatCsvImporter import SciChatCsvImporter


class SciChatSaver(CsvSaver):
    def __init__(self, options):
        # Create an EventLogCsvImporter object with no corresponding CSV file:
        lookup_active_flight(options)
        self.importer = SciChatCsvImporter(options['config_yaml'], None,
                                    options['vehicle'],
                                    options['flight']) #,
                                    #options['timezone'],
                                    #options['input'],
                                    #options['reload'],
                                    #options['replace'],
                                    #options['skip_bad'])
        self.delimiter = self.importer.config['delimiter']
        TelemetrySaver.__init__(self, options)


if __name__=='__main__':
    with open('redis_scichat_saver_config.yaml', 'r') as fp:
        config = yaml.load(fp)

    verbose = False
    if 'verbose' in config:
        verbose = config['verbose']

    if 'savers' in config:
        savers = []
        for name, params in config['savers'].iteritems():
            savers.append(SciChatSaver(params))
        while True:
            sleep(1)