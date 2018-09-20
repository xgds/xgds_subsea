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

#import json
#from django.db import models
from django.test import TestCase
#from django.core.urlresolvers import reverse
#from django.http import HttpResponseForbidden, Http404, JsonResponse
from django.contrib.auth.models import User

from xgds_subsea_app.importer.create_users import *


class TestCreateUsers(TestCase):

    fixtures = ['test_create_users.json']

    """
    Tests for create_users.py
    """

    def test_user_exists(self):
        self.assertTrue(user_exists('Bob','Wayne'))
        self.assertFalse(user_exists('Bruce','Wayne'))

    def test_username_exists(self):
        self.assertTrue(username_exists('bwayne'))
        self.assertFalse(username_exists('ckent'))

    def test_generate_username(self):
        self.assertEqual('bwayne1', get_new_username_from_name('Bruce Wayne'))
        self.assertEqual('pparker', get_new_username_from_name('Peter Parker'))
        self.assertEqual('jdyne', get_new_username_from_name('Janet van Dyne'))

    def test_create_users(self):
        created = create_users('apps/xgds_subsea_app/test/test_files/cruise-record.xml')
        self.assertEqual(3,created) # should have created 3 new users
        assert(user_exists('Bob','Wayne'))
        assert(user_exists('Bruce','Wayne'))
        assert(user_exists('Peter','Parker'))
        assert(username_exists('bwayne'))
        assert(username_exists('bwayne1'))
        assert(username_exists('jdyne'))