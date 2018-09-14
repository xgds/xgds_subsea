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


class xgds_subsea_appTest(TestCase):

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









