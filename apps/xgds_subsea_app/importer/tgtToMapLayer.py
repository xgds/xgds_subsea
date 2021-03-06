#!/usr/bin/env python
# __BEGIN_LICENSE__
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
import csv
import os
import json
import django
django.setup()

from django.conf import settings

from django.utils import timezone
from dateutil.parser import parse as dateparser
from datetime import datetime
from uuid import uuid4, UUID
from geocamUtil.models import SiteFrame

from xgds_map_server.models import MapGroup
from xgds_map_server.models import MapLayer
from django.core.serializers.json import DjangoJSONEncoder


WHITE = '#ffffff'

def initialize_map_layer(filepath, cruiseID, region=0):
    map_layer = MapLayer()

    nameparts = os.path.basename(filepath).split('.')
    map_layer.name = '%s_%s' % (cruiseID, nameparts[0])
    map_layer.description = 'Imported from Hypack file'
    map_layer.creator = 'Importer'
    map_layer.creation_time = timezone.now()
    map_layer.uuid = uuid4()
    map_layer.parentId = 'targets'
    map_layer.parent = MapGroup.objects.get(uuid='targets')
    map_layer.region = SiteFrame.objects.get(id=region)
    map_layer.defaultColor = WHITE
    return map_layer


# class UUIDEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, UUID):
#             # if the obj is uuid, we simply return the value of uuid
#             return obj.hex
#         return json.JSONEncoder.default(self, obj)


def process_row(map_layer, row, jsonString, minLat, minLon, maxLat, maxLon):
    if row:
        new_station={}
        new_station['mapLayer'] = map_layer.uuid
        new_station['mapLayerName'] = map_layer.name
        new_station['type'] = "Station"
        new_station['name'] = row[1]
        new_station['description'] = row[14]
        float_lon = float(row[6])
        float_lat = float(row[5])

        new_station['point'] = [float_lon, float_lat]
        if float_lat < minLat:
            minLat = float_lat
        if float_lat > maxLat:
            maxLat = float_lat
        if float_lon < minLon:
            minLon = float_lon
        if float_lon > maxLon:
            maxLon = float_lon

        new_station['depth'] = row[4]
        new_station['timestamp'] = dateparser(str(row[7] + " " + str(row[8])))
        new_station['uuid'] = uuid4()
        new_station['style'] = WHITE
        jsonString = jsonString + json.dumps(new_station, indent=4, sort_keys=True, cls=DjangoJSONEncoder) + ","
        return jsonString, minLat, minLon, maxLat, maxLon
    raise Exception('Empty row in *.tgt file, panicking')


def import_tgt_map_layer(filepath, cruiseID, region=0):
    """
    Import a SURVEY.tgt file as a Map Layer
    :param filepath: full path to the file
    :param cruiseID: i.e. NA100
    :param region: number, i.e. 2
    :return:
    """
    if os.stat(filepath).st_size == 0:
        raise Exception('The *.tgt file was empty, nothing to import')

    map_layer = initialize_map_layer(filepath, cruiseID, region)

    file = open(filepath, 'rbU')
    reader = csv.reader(file, delimiter=' ', quotechar='"')

    minLat = 360
    minLon = 360
    maxLat = -360
    maxLon = -360
    jsonString = '{"features":['

    for row in reader:
        jsonString, minLat, minLon, maxLat, maxLon = \
            process_row(map_layer, row, jsonString, minLat, minLon, maxLat, maxLon)

    map_layer.minLat = minLat
    map_layer.minLon = minLon
    map_layer.maxLat = maxLat
    map_layer.maxLon = maxLon

    # lop off the last comma and close the brackets
    map_layer.jsonFeatures = jsonString[:-1] + ']}'
    map_layer.save()

    return map_layer


if __name__=='__main__':
    try:
        filepath = sys.argv[1]
    except:
        print "Please enter a file to parse"
        sys.exit(-1)

    print 'importing %s' % filepath
    map_layer = import_tgt_map_layer(filepath, settings.CRUISE_ID, settings.XGDS_CURRENT_SITEFRAME_ID)
    if map_layer:
        sys.exit(0)
    else:
        print 'map layer not created'
        sys.exit(-1)


