#! /usr/bin/env python
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

import django
django.setup()

import eventLogCsvImporter


def main():
    import optparse

    parser = optparse.OptionParser('usage: -c config -i input')
    parser.add_option('-c', '--config', help='path to config file (yaml)')
    parser.add_option('-i', '--input', help='path to csv file to import')
    # parser.add_option('-v', '--vehicle', help='name of vehicle')
    # parser.add_option('-f', '--flight', help='name of flight')
    parser.add_option("-r", '--reload', action="store_true", dest="reload", default=False, help="force reload")
    parser.add_option("-p", '--replace', action="store_true", dest="replace", default=False,
                      help="replace existing data, you probably also want -r")
    # parser.add_option('-z', '--timezone', help='timezone, defaults to UTC.  example: America/Los_Angeles')
    parser.add_option('-s', '--skip_bad', action="store_true", dest="skip_bad", default=False,
                      help='Skip bad rows, importing all other data')

    opts, args = parser.parse_args()

    if not opts.config:
        parser.error('config is required')
    if not opts.input:
        parser.error('input is required')

    importer = eventLogCsvImporter.EventLogCsvImporter(opts.config, opts.input, force=opts.reload, replace=opts.replace, skip_bad=opts.skip_bad)
    result = importer.load_csv()

    print 'loaded %d ' % len(result)


if __name__ == '__main__':
    main()
