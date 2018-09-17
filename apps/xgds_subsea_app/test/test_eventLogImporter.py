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

import json
from django.db import models
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, Http404, JsonResponse

from xgds_subsea_app.importer.eventLogCsvImporter import *
from xgds_notes2.models import HierarchichalTag, LocatedNote

from django.contrib.auth.models import User


class eventLogImporterTest(TestCase):

    fixtures = ['initial_data.json', 'users.json', 'note_locations.json', 'note_roles.json', 'note_tags.json']

    """
    Tests for the eventLogCsvImporter
    """

    def test_clean_key_value(self):
        key, value = clean_key_value(None)
        self.assertIsNone(key)
        self.assertIsNone(value)
        key, value = clean_key_value('hi')
        self.assertIsNone(key)
        self.assertIsNone(value)
        key, value = clean_key_value({'TEST': 'NaN'})
        self.assertEqual(key, 'TEST')
        self.assertIsNone(value)
        key, value = clean_key_value({'TEST': 'hello_there'})
        self.assertEqual(key, 'TEST')
        self.assertEqual(value, 'hello there')

    def test_clean_append(self):
        result = clean_append(None, None)
        self.assertIsNone(result)
        result = clean_append(None, 'something')
        self.assertEqual(result, 'something')
        result = clean_append('something', None)
        self.assertEqual(result, 'something')
        result = clean_append('something', 'else')
        self.assertEqual(result, 'somethingelse')

    def test_remove_empty_keys(self):
        dictionary = {'test': 1,
                      None: 2}
        self.assertEqual(len(dictionary.keys()), 2)
        result = remove_empty_keys(dictionary)
        self.assertEqual(len(dictionary.keys()), 1)

    def test_append_key_value(self):
        result = append_key_value(None, None, None)
        self.assertIsNone(result)
        result = append_key_value(None, 'B', None)
        self.assertIsNone(result)
        result = append_key_value(None, None, 'C')
        self.assertIsNone(result)
        result = append_key_value(None, 'B', 'C')
        self.assertEqual(result, 'B: C')
        result = append_key_value('A', 'B', None)
        self.assertEqual(result, 'A')
        result = append_key_value('A', None, 'C')
        self.assertEqual(result, 'A')
        result = append_key_value('A', 'B', 'C')
        self.assertEqual(result, 'A\nB: C')

    def test_add_tag(self):
        row = {}
        add_tag(row, None)
        self.assertFalse('tag' in row)
        add_tag(row, 'lower')
        self.assertTrue('tag' in row)
        self.assertTrue('lower' in row['tag'])
        add_tag(row, 'capitalize', True)
        self.assertTrue('Capitalize' in row['tag'])
        pass

    def test_add_notes_tag(self):
        row = {}
        add_notes_tag(row, None)
        self.assertFalse('tag' in row)
        add_notes_tag(row, 'Trash')
        self.assertTrue('Trash' in row['tag'])
        add_notes_tag(row, 'Biology')
        self.assertTrue('Biology' in row['tag'])
        add_notes_tag(row, 'Geology')
        self.assertTrue('Geology' in row['tag'])
        add_notes_tag(row, 'T-ROV')
        self.assertTrue('TempProbe' in row['tag'])
        add_notes_tag(row, 'T-IGT')
        self.assertTrue('TempIGT' in row['tag'])
        add_notes_tag(row, 'T-SUPR')
        self.assertTrue('TempSUPR' in row['tag'])

    def test_add_sample_type_tag(self):
        row = {}
        add_sample_type_tag(row, None)
        self.assertFalse('tag' in row)
        add_sample_type_tag(row, 'SUPR')
        self.assertTrue('SUPR' in row['tag'])
        add_sample_type_tag(row, 'IGT')
        self.assertTrue('IGT' in row['tag'])
        add_sample_type_tag(row, 'ROVG')
        self.assertTrue('ROVGrab' in row['tag'])
        add_sample_type_tag(row, 'ROVPC')
        self.assertTrue('PushCore' in row['tag'])
        add_sample_type_tag(row, 'Niskin')
        self.assertTrue('Niskin' in row['tag'])

    def test_add_divestatus_tag(self):
        row = {}
        add_divestatus_tag(row, None)
        self.assertFalse('tag' in row)
        add_divestatus_tag(row, 'onbottom')
        self.assertTrue('OnBottom' in row['tag'])
        add_divestatus_tag(row, 'offbottom')
        self.assertTrue('OffBottom' in row['tag'])
        add_divestatus_tag(row, 'inwater')
        self.assertTrue('InWater' in row['tag'])
        add_divestatus_tag(row, 'ondeck')
        self.assertTrue('OnDeck' in row['tag'])

    def test_add_audiovideo_rating_tag(self):
        row = {}
        add_audiovideo_rating_tag(row, None)
        self.assertFalse('tag' in row)
        add_audiovideo_rating_tag(row, '0')
        self.assertTrue('Rating0' in row['tag'])
        add_audiovideo_rating_tag(row, 1)
        self.assertTrue('Rating1' in row['tag'])
        add_audiovideo_rating_tag(row, 2)
        self.assertTrue('Rating2' in row['tag'])
        add_audiovideo_rating_tag(row, 3)
        self.assertTrue('Rating3' in row['tag'])
        add_audiovideo_rating_tag(row, 4)
        self.assertTrue('Rating4' in row['tag'])
        add_audiovideo_rating_tag(row, 5)
        self.assertTrue('Rating5' in row['tag'])

    def test_load_csv(self):
        """
        Actually test loading a csv file into a database
        :return:
        """

        importer = EventLogCsvImporter('/home/xgds/xgds_subsea/apps/xgds_subsea_app/importer/EventLog.yaml',
                                       '/home/xgds/xgds_subsea/apps/xgds_subsea_app/test/test_files/eventlog.txt',
                                       force=False,
                                       replace=False,
                                       skip_bad=True)
        result = importer.load_csv()
        # Should show the number of records imported
        self.assertEqual(len(result), 37)








