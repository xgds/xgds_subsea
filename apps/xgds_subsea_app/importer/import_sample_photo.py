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
import os

import django
django.setup()

from django.core.exceptions import ObjectDoesNotExist

from xgds_sample.models import Sample
from xgds_image.importer.import_image import import_image
from xgds_image.models import ImageSet
from ImportUtil import link_sample_and_image

"""
Import a sample photo, either connecting it to the sample or doing the import and connecting it to the sample.
Currently the connection to the sample is done via a note.
"""


def lookup_sample(filename):
    # find the name of the sample
    tokens = filename.split('/')
    sampleID = tokens[len(tokens) - 3]
    # print 'looking up ' + str(sampleID)
    try:
        sample = Sample.objects.get(name=sampleID)  # NA100-123 for example
        # print 'Timestamp for ' + str(sampleID) + ' is ' + str(sample.collection_time)
        return sample
    except ObjectDoesNotExist as e:
        # TODO what do we do in this case?  I think fail
        msg = "Could not find sample for %s. " % sampleID
        print msg
        e.message = msg + e.message
        raise e


if __name__=='__main__':
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-c', '--camera',
                      help='Name of the camera this image came from', default='LabCamera')
    parser.add_option('-s', '--serial',
                      help='Serial number of the camera this image came from')
    parser.add_option('-u', '--username', default='irg', help='username for xgds auth')
    parser.add_option('-p', '--password', help='authtoken for xgds authentication.  Can get it from https://xgds_server_name/accounts/rest/genToken/<username>')
    parser.add_option('-i', '--importimage', action='store_true', dest='importimage',
                      help='Do the import of this image file')

    opts, args = parser.parse_args()
    filename = args[0]
    sample = lookup_sample(filename)
    retval = 0
    if opts.importimage:
        timestamp = sample.collection_time
        retval = import_image(filename, camera=opts.camera, username=opts.username, password=opts.password,
                              camera_serial=opts.serial, timestamp=timestamp)

    # make a note on the image to link it to the sample
    try:
        image_set = ImageSet.objects.get(name=os.path.basename(filename))
        link_sample_and_image(sample, image_set)
    except ObjectDoesNotExist as e:
        print 'Image does not exist for %s' % filename
        raise e

    sys.exit(retval)