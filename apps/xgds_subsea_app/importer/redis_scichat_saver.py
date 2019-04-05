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
from time import sleep

import django
django.setup()

from redis_csv_saver import CsvSaver
from sciChatCsvImporter import SciChatCsvImporter


class SciChatSaver(CsvSaver):

    def construct_importer(self, options):
        return SciChatCsvImporter(options['config_yaml'], None,
                                  options['vehicle'])


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
        savers.append(SciChatSaver(params))
    while True:
        sleep(1)
