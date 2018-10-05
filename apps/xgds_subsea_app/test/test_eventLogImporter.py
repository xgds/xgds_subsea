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

from xgds_subsea_app.importer.eventLogCsvImporter import *
from xgds_notes2.models import HierarchichalTag, LocatedNote
from xgds_sample.models import Sample, Label


class eventLogImporterTest(TestCase):

    fixtures = ['initial_data.json', 'users.json', 'note_locations.json', 'note_roles.json', 'note_tags.json', \
                'test_eventlog_users.json', ]

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
                      None: 2,
                      '': 3}
        self.assertEqual(len(dictionary.keys()), 3)
        dictionary = remove_empty_keys(dictionary)
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
        add_notes_tag(row, 'Other')
        self.assertTrue('Other' in row['tag'])

    def test_add_sample_type_tag(self):
        row = {}
        add_sample_type_tag(row, None)
        self.assertFalse('tag' in row)
        add_sample_type_tag(row, 'SUPR-1')
        self.assertTrue('SUPR-1' in row['tag'])
        add_sample_type_tag(row, 'SUPR2')
        self.assertTrue('SUPR-2' in row['tag'])
        add_sample_type_tag(row, 'IGT')
        self.assertTrue('IGT' in row['tag'])
        add_sample_type_tag(row, 'ROVG')
        self.assertTrue('ROVGrab' in row['tag'])
        add_sample_type_tag(row, 'ROVPC')
        self.assertTrue('PushCore' in row['tag'])
        add_sample_type_tag(row, 'scoop')
        self.assertTrue('Scoop' in row['tag'])
        add_sample_type_tag(row, 'Niskin')
        self.assertTrue('Niskin' in row['tag'])
        row = {}
        add_sample_type_tag(row, 'NISKINS')
        self.assertTrue('Niskin' in row['tag'])
        row = {}
        add_sample_type_tag(row, 'NISKIN')
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
        result = add_audiovideo_rating_tag(row, None)
        self.assertFalse('tag' in row)
        self.assertEqual(result, 'NO VALUE')
        result = add_audiovideo_rating_tag(row, '0')
        self.assertTrue('Rating0' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 1)
        self.assertTrue('Rating1' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 2)
        self.assertTrue('Rating2' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 3)
        self.assertTrue('Rating3' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 4)
        self.assertTrue('Rating4' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 5)
        self.assertTrue('Rating5' in row['tag'])
        self.assertTrue(result)
        result = add_audiovideo_rating_tag(row, 6)
        self.assertFalse('Rating6' in row['tag'])
        self.assertFalse(result)
        result = add_audiovideo_rating_tag(row, 1.5)
        self.assertFalse('Rating1.5' in row['tag'])
        self.assertFalse(result)


    def test_add_timing_data_tag(self):
        row = {}
        result = add_timing_or_data_tag(row, None)
        self.assertEqual(result, "NO VALUE")
        result = add_timing_or_data_tag(row, "MIN")
        self.assertTrue('Min' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "max")
        self.assertTrue('Max' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "avg")
        self.assertTrue('Average' in row['tag'])
        self.assertTrue(result)
        row = {}
        result = add_timing_or_data_tag(row, "average")
        self.assertTrue('Average' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "end")
        self.assertTrue('End' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "start")
        self.assertTrue('Start' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "restart")
        self.assertTrue('Resume' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "pause")
        self.assertTrue('Pause' in row['tag'])
        self.assertTrue(result)
        row = {}
        result = add_timing_or_data_tag(row, "resume")
        self.assertTrue('Resume' in row['tag'])
        self.assertTrue(result)
        result = add_timing_or_data_tag(row, "stop")
        self.assertTrue('Stop' in row['tag'])
        self.assertTrue(result)

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

        sampleTag = HierarchichalTag.objects.get(name='sample')
        self.assertEqual(sampleTag.xgds_notes2_taggednote_related.count(), 11)
        igtTag = HierarchichalTag.objects.get(name='IGT')
        self.assertEqual(igtTag.xgds_notes2_taggednote_related.count(), 2)
        suprTag = HierarchichalTag.objects.get(name='SUPR-1')
        self.assertEqual(suprTag.xgds_notes2_taggednote_related.count(), 8)
        grabTag = HierarchichalTag.objects.get(name='ROVGrab')
        self.assertEqual(grabTag.xgds_notes2_taggednote_related.count(), 1)

        diveStatusTag = HierarchichalTag.objects.get(name='DiveStatus')
        self.assertEqual(diveStatusTag.xgds_notes2_taggednote_related.count(), 6)

        audioVideoTag = HierarchichalTag.objects.get(name='AudioVideo')
        self.assertEqual(audioVideoTag.xgds_notes2_taggednote_related.count(), 3)

        engineeringTag = HierarchichalTag.objects.get(name='Engineering')
        self.assertEqual(engineeringTag.xgds_notes2_taggednote_related.count(), 1)

        self.assertEqual(result[0].content, 'inwater')
        self.assertTrue('inwater' in result[0].content)
        self.assertTrue('inwater' in result[0].tags.slugs())
        self.assertEqual(result[0].tags.count(), 2)

        self.assertEqual(result[1].content, 'Argus in water')

        samples = Sample.objects.all()
        self.assertEqual(samples.count(), 11)
        self.assertEqual(samples[0].name, 'NA100-001')
        self.assertEqual(samples[0].label.number, 100001)

        igtsamples = Sample.objects.filter(sample_type__pk=1)
        self.assertEqual(igtsamples.count(), 2)

        grabsamples = Sample.objects.filter(sample_type__pk=4)
        self.assertEqual(grabsamples.count(), 1)

        suprsamples = Sample.objects.filter(sample_type__pk=5)
        self.assertEqual(suprsamples.count(), 8)









