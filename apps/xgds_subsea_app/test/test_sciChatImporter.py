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

from dateutil.parser import parse as dateparser
import pytz

from django.test import TransactionTestCase
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, Http404, JsonResponse

from xgds_subsea_app.importer.sciChatCsvImporter import *
from xgds_notes2.models import LocatedMessage

from django.contrib.auth.models import User


class chatLogImporterTest(TransactionTestCase):

    fixtures = ['xgds_subsea_app_initial_data.json',
                'users.json',]

    """
    Tests for the chatLogCsvImporter
    """

    def test_clean_author(self):
        row = {'author_name': 'datalogger'}
        result = clean_author(row)
        self.assertFalse('author_name' in result)
        self.assertTrue('author' in result)
        self.assertIsInstance(result['author'], User)
        self.assertTrue(result['author'].pk, 12)

        row = {'author_name': 'ChiefSci'}
        result = clean_author(row)
        self.assertFalse('author_name' in result)
        self.assertTrue('author' in result)
        self.assertIsInstance(result['author'], User)
        self.assertTrue(result['author'].pk, 14)

        row = {'author_name': 'TestUser'}
        result = clean_author(row)
        self.assertFalse('author_name' in result)
        self.assertTrue('author' in result)
        self.assertIsInstance(result['author'], User)
        self.assertTrue(result['author'].first_name, 'Test')
        self.assertTrue(result['author'].last_name, 'User')

        with self.assertRaises(KeyError) as no_author:
            row = {}
            result = clean_author(row)
        self.assertTrue('Row does not contain author_name' in no_author.exception.message)

        with self.assertRaises(AssertionError) as blank_author:
            row = {'author_name': ''}
            result = clean_author(row)
        self.assertTrue('Author name is empty' in blank_author.exception.message)

    def test_load_csv(self):
        """
        Actually test loading a csv file into a database
        :return:
        """

        importer = SciChatCsvImporter('/home/xgds/xgds_subsea/apps/xgds_subsea_app/importer/SciChat.yaml',
                                       '/home/xgds/xgds_subsea/apps/xgds_subsea_app/test/test_files/chatlog.txt',
                                       force=False,
                                       replace=False,
                                       skip_bad=True)
        result = importer.load_csv()
        # Should show the number of records imported
        self.assertEqual(len(result), 40)
        self.assertIsInstance(result[0], LocatedMessage)
        self.assertEqual(result[0].content, 'test')
        self.assertEqual(result[0].author.pk, 12)
        d = dateparser('2018-08-29T09:56:28.372Z').replace(tzinfo=pytz.utc)
        self.assertEqual(result[0].event_time, d)

        chief_sci_messages = LocatedMessage.objects.filter(author__pk=14)
        self.assertEqual(chief_sci_messages.count(), 11)









