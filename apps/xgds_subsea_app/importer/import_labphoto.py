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

import django
django.setup()
from xgds_sample.models import *
from xgds_image.importer.import_image import import_image


def parse_timestamp(filename):
    # find the name of the sample
    tokens = filename.split('/')
    sampleID = tokens[len(tokens) - 3]
    print 'looking up ' + str(sampleID)
    sample = Sample.objects.get(name=sampleID)  # NA100-123 for example
    print 'Timestamp for ' + str(sampleID) + ' is ' + str(sample.collection_time)
    return sample.collection_time


if __name__=='__main__':
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-c', '--camera',
                      help='Name of the camera this image came from')
    parser.add_option('-s', '--serial',
                      help='Serial number of the camera this image came from')
    parser.add_option('-u', '--username', default='irg', help='username for xgds auth')
    parser.add_option('-p', '--password', help='authtoken for xgds authentication.  Can get it from https://xgds_server_name/accounts/rest/genToken/<username>')

    opts, args = parser.parse_args()
    camera = opts.camera
    filename = args[0]
    timestamp = parse_timestamp(filename)
    retval = import_image(filename, camera=camera, username=opts.username, password=opts.password, camera_serial=opts.serial, timestamp=timestamp)
    sys.exit(retval)