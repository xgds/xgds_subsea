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

from django.test import TestCase
from django.utils import timezone
from xgds_subsea_app.importer.tgtToMapLayer import *
from geocamUtil.models import SiteFrame
from xgds_map_server.models import MapGroup


# also test exceptions/bad input self.assertRaises()
class tgtToMapLayerTest(TestCase):
    fixtures = ['site_frames.json',
                'xgds_subsea_app_initial_data.json']

    filepath = '/home/xgds/xgds_subsea/apps/xgds_subsea_app/test/test_files/SURVEY.tgt'
    cruiseId = 'CROOZ_WUN'
    region = 2

    def verify_uuid(self, uuid):
        uuid_tokens = str(uuid).split('-')
        self.assertEqual(len(uuid_tokens), 5)
        self.assertEqual(len(uuid_tokens[0]), 8)
        self.assertEqual(len(uuid_tokens[1]), 4)
        self.assertEqual(len(uuid_tokens[2]), 4)
        self.assertEqual(len(uuid_tokens[3]), 4)
        self.assertEqual(len(uuid_tokens[4]), 12)

    def test_initialize_map_layer(self):
        ml = initialize_map_layer(tgtToMapLayerTest.filepath, tgtToMapLayerTest.cruiseId, tgtToMapLayerTest.region)
        near_creation_time = timezone.now()
        self.assertEqual(ml.name, tgtToMapLayerTest.cruiseId + '_SURVEY')
        self.assertEqual(ml.description, 'Imported from Hypack file')
        self.assertEqual(ml.creator, 'Importer')
        time_diff = near_creation_time - ml.creation_time
        self.assertLess(time_diff.seconds, 1)
        self.verify_uuid(ml.uuid)

        self.assertEqual(ml.parent, MapGroup.objects.get(uuid='targets'))
        self.assertEqual(ml.region, SiteFrame.objects.get(id=tgtToMapLayerTest.region))

        self.assertEqual(ml.deleted, 0)
        self.assertEqual(ml.locked, 0)
        self.assertEqual(ml.visible, 0)
        self.assertEqual(ml.transparency, 0)
        self.assertEqual(ml.defaultColor, '#ffffff')

    def test_process_row(self):
        ml = initialize_map_layer(tgtToMapLayerTest.filepath, tgtToMapLayerTest.cruiseId, tgtToMapLayerTest.region)

        row = ['GPT',
                "Label 1",
                262280.26,
                2091992.15,
                44.4,
                20,
                -150,
                '12:34:56',
                '01/02/2003',
                0.00,
                0.00,
                99,
                0,
                0.00,
                "Poetical, lyrical, vivid description",
                "",
                0.0]

        jsonString, minLat, minLon, maxLat, maxLon = \
            process_row(ml, row, "", 360, 360, -360, -360)

        self.assertEqual(minLat, 20)
        self.assertEqual(maxLat, 20)
        self.assertEqual(minLon, -150)
        self.assertEqual(maxLon, -150)

        depth_string = '"depth": 44.4'
        description_string = '"description": "Poetical, lyrical, vivid description"'
        maplayer_name_string = '"mapLayerName": "CROOZ_WUN_SURVEY"'
        name_string = '"name": "Label 1"'
        time_string = '"timestamp": "2003-01-02T12:34:56"'
        type_string = '"type": "Station"'

        self.assertTrue(depth_string in jsonString)
        self.assertTrue(description_string in jsonString)
        self.assertTrue(maplayer_name_string in jsonString)
        self.assertTrue(name_string in jsonString)
        self.assertTrue(time_string in jsonString)
        self.assertTrue(type_string in jsonString)

        no_whitespace = ''.join(jsonString.split())
        point_string = '"point":[-150,20]'
        self.assertTrue(point_string in no_whitespace)

    def test_import_tgt_map_layer(self):
        retval = import_tgt_map_layer(tgtToMapLayerTest.filepath, tgtToMapLayerTest.cruiseId, tgtToMapLayerTest.region)

        ml = MapLayer.objects.get(name="CROOZ_WUN_SURVEY")
        self.assertTrue(ml)

        self.assertEqual(ml.minLat, -89.1)
        self.assertEqual(ml.maxLat,  50.5)
        self.assertEqual(ml.minLon, -150.2)
        self.assertEqual(ml.maxLon,  100.7)

        the_json = json.loads(str(ml.jsonFeatures))
        self.assertEqual(float(the_json['features'][0]['depth']), 10.0)
        self.assertEqual(float(the_json['features'][1]['depth']), 20.0)
        self.assertEqual(float(the_json['features'][2]['depth']), 30.0)
        self.assertEqual(float(the_json['features'][3]['depth']), 40.0)

        self.verify_uuid(the_json['features'][0]['mapLayer'])
        self.verify_uuid(the_json['features'][1]['mapLayer'])
        self.verify_uuid(the_json['features'][2]['mapLayer'])
        self.verify_uuid(the_json['features'][3]['mapLayer'])

        self.verify_uuid(the_json['features'][0]['uuid'])
        self.verify_uuid(the_json['features'][1]['uuid'])
        self.verify_uuid(the_json['features'][2]['uuid'])
        self.verify_uuid(the_json['features'][3]['uuid'])

        self.assertEqual(the_json['features'][0]['mapLayerName'], 'CROOZ_WUN_SURVEY')
        self.assertEqual(the_json['features'][1]['mapLayerName'], 'CROOZ_WUN_SURVEY')
        self.assertEqual(the_json['features'][2]['mapLayerName'], 'CROOZ_WUN_SURVEY')
        self.assertEqual(the_json['features'][3]['mapLayerName'], 'CROOZ_WUN_SURVEY')

        self.assertEqual(the_json['features'][0]['type'], 'Station')
        self.assertEqual(the_json['features'][1]['type'], 'Station')
        self.assertEqual(the_json['features'][2]['type'], 'Station')
        self.assertEqual(the_json['features'][3]['type'], 'Station')

        self.assertEqual(the_json['features'][0]['timestamp'], '2009-07-08T12:34:56')
        self.assertEqual(the_json['features'][1]['timestamp'], '2014-12-13T23:22:21')
        self.assertEqual(the_json['features'][2]['timestamp'], '2008-08-08T08:08:08')
        self.assertEqual(the_json['features'][3]['timestamp'], '2015-05-15T15:15:15')

        self.assertEqual(the_json['features'][0]['name'], 'Captain Nemo\'s Hideaway')
        self.assertEqual(the_json['features'][1]['name'], 'Ursula\'s Lair')
        self.assertEqual(the_json['features'][2]['name'], 'Atlantis')
        self.assertEqual(the_json['features'][3]['name'], 'Sebastien\'s Rehearsal Room')

        self.assertEqual(the_json['features'][0]['description'], 'A cave big enough for the original Nautilus')
        self.assertEqual(the_json['features'][1]['description'], 'Where the octopus-queen hangs out with friends Flotsam and Jetsam')
        self.assertEqual(the_json['features'][2]['description'], 'Shhhhhh!')
        self.assertEqual(the_json['features'][3]['description'], 'That crab never stops composing')

        self.assertEqual(the_json['features'][0]['point'][0], "-150.2")
        self.assertEqual(the_json['features'][0]['point'][1], "20.01")

        self.assertEqual(the_json['features'][1]['point'][0], "-40.2")
        self.assertEqual(the_json['features'][1]['point'][1], "50.5")

        self.assertEqual(the_json['features'][2]['point'][0], "28.009")
        self.assertEqual(the_json['features'][2]['point'][1], "-23.2")

        self.assertEqual(the_json['features'][3]['point'][0], "100.7")
        self.assertEqual(the_json['features'][3]['point'][1], "-89.1")
