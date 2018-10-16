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

from xgds_subsea_app.importer.eventLogCsvImporter import EventLogCsvImporter
from xgds_subsea_app.importer.sampleSummaryImporter import clean_value, import_sample_summary

from xgds_sample.models import Sample


class SampleSummaryImporterTest(TestCase):

    fixtures = ['xgds_subsea_app_initial_data.json',
                'test_eventlog_users.json', ]

    """
    Tests for the sample summary importer
    """

    def test_clean_value(self):
        """
        Test the clean value function from sample summary importer
        :return:
        """
        self.assertIsNone(clean_value(''))
        self.assertIsNone(clean_value('N/A'))
        self.assertIsNone(clean_value('n/a'))
        self.assertIsNone(clean_value(' n/a'))
        self.assertEqual('test', clean_value('test'))

    def test_load_samples_summary(self):
        """
        Test loading the samples summary file, which will populate the extras from the samples
        loaded from the prior event log importer test
        :return:
        """

        # precreate the samples by loading the event log
        importer = EventLogCsvImporter('/home/xgds/xgds_subsea/apps/xgds_subsea_app/importer/EventLog.yaml',
                                       '/home/xgds/xgds_subsea/apps/xgds_subsea_app/test/test_files/eventlog.txt',
                                       force=False,
                                       replace=False,
                                       skip_bad=True)
        result = importer.load_csv()

        count = import_sample_summary('/home/xgds/xgds_subsea/apps/xgds_subsea_app/test/test_files/samples.xlsx')
        self.assertEqual(count, 11)
        sample = Sample.objects.get(name='NA100-011')
        extras = sample.extras
        self.assertIsNotNone(extras)
        self.assertEqual(extras['wetlab_description'], '22.5x12cm. Test description.')
        self.assertEqual(extras['preservation'], 'Dry')
        self.assertEqual(extras['recipient'], 'SKN')
        self.assertEqual(extras['storage'], 'Box 6')
        self.assertEqual(extras['other_notes'], 'Please return to GSO when analysis complete')

