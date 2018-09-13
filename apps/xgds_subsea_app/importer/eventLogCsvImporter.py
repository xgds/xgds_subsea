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

from geocamUtil.UserUtil import getUserByUsername, getUserByNames
from xgds_core.importer import csvImporter
from xgds_core.FlightUtils import lookup_flight
from xgds_notes2.models import LocatedNote, HierarchichalTag, TaggedNote, Role, Location


class EventLogCsvImporter(csvImporter.CsvImporter):
    """
    Utilities for loading event log files from files such as <cruise>/processed/eventlog/by-dive/all_eventlog_<DIVE>.txt
    This will create notes with references to the correct users, roles, locations and tags.
    It will skip sample creation, as samples are recorded separately
    """

    datalogger_user = getUserByUsername('datalogger')
    navigator_user = getUserByUsername('navigator')
    scf_user = getUserByUsername('scf')

    # tags = {}
    # tags['EVENTLOG'] = HierarchichalTag.objects.get(name='EventLog')
    # tags['OBJECTIVE'] = HierarchichalTag.objects.get(name='Objective')
    # tags['SAMPLE'] = HierarchichalTag.objects.get(name='Sample')
    # tags['AUDIOVIDEO'] = HierarchichalTag.objects.get(name='AudioVideo')
    # tags['DIVESTATUS'] = HierarchichalTag.objects.get(name='DiveStatus')
    # tags['TRASH'] = HierarchichalTag.objects.get(name='Trash')
    # tags['ENGINEERING'] = HierarchichalTag.objects.get(name='Engineering')
    # tags['MULTIBEAMLINE'] = HierarchichalTag.objects.get(name='MultibeamLine')

    roles = {}
    roles['NAVIGATOR'] = Role.objects.get(value='NAVIGATOR')
    roles['SCF'] = Role.objects.get(value='SCIENCE_COMMUNICATION_FELLOW')
    roles['DATA_LOGGER'] = Role.objects.get(value='DATA_LOGGER')

    ship_location = Location.objects.get(value='SHIP')

    def check_data_exists(self, row):
        """
        See if there is already identical data
        :param row: typically the first row
        :return: True if it already exists, false otherwise
        """
        row = self.update_row(row)
        row_copy = row.copy()
        del row_copy['tag']
        if row:
            result = LocatedNote.objects.filter(**row_copy)
            return result.exists()
        return False

    def update_row(self, row):
        """
        Update the row from the self.config
        :param row: the loaded row
        :return: the updated row, with timestamps and defaults
        """
        result = super(EventLogCsvImporter, self).update_row(row)

        result = self.clean_key_values(result)
        if result:
            result = self.clean_author(result)
            result = self.clean_flight(result)
            result = self.sanitize(result)
            result['location'] = self.ship_location

        return result

    def sanitize(self, row):
        """
        Remove all unneccessary things from the dictionary
        :param row:
        :return:
        """
        if None in row:
            del row[None]
        return row

    def clean_author(self, row):
        """
        Updates the row by looking up the correct author id by the name
        Also figure out the role based on the author.  Defaults to DATA_LOGGER
        :param row:
        :return: the updated row
        """
        author_name = row['author_name']
        lower_name = author_name.lower()
        if author_name.lower() == 'nav' or lower_name == 'navigator' or lower_name == 'navigation':
            row['role'] = self.roles['NAVIGATOR']
            row['author'] = self.navigator_user
        elif author_name.lower() == 'default_scf_user':
            row['role'] = self.roles['SCIENCE_COMMUNICATION_FELLOW']
            row['author'] = self.scf_user
        else:
            row['role'] = self.roles['DATA_LOGGER']
            splits = author_name.split('_')
            if len(splits) == 2:
                try:
                    row['author'] = getUserByNames(splits[0], splits[1])
                except:
                    # TODO will we ever be in this state?
                    pass

        if 'author' not in row:
            row['author'] = self.datalogger_user

        del row['author_name']

        return row

    def clean_flight(self, row):
        """
        Updates the row by looking up the correct flight id by the name.
        Hardcoding to Hercules vehicle
        :param row:
        :return: the updated row
        """
        flight_name = row['group_flight_name'] + '_' + self.vehicle.name
        row['flight'] = lookup_flight(flight_name)
        del row['group_flight_name']
        return row

    def clean_key_value(self, dictionary):
        """
        Return a tuple including the key and value string replacing underscores with spaces
        :param dictionary: should have one entry
        :return: None if it is NaN, or the cleaned value string
        """
        if not dictionary:
            return None, None
        if not isinstance(dictionary, dict):
            return None, None
        key = dictionary.keys()[0]
        value_string = dictionary.values()[0]
        if value_string == 'NaN':
            return key, None
        value_string = value_string.replace('_', ' ')
        return key, value_string

    def clean_append(self, part_1, part_2):
        if part_1:
            if part_2:
                return part_1 + part_2
            return part_1
        return part_2

    def append_key_value(self, content, key, value):
        """
        Safely append the key/value as a separate line to the content
        :param content:
        :param key:
        :param value:
        :return: new content
        """
        if value and key:
            if content:
                return '%s\n%s: %s' % (content, key, value)
            return '%s: %s' % (key, value)
        return content


    def clean_key_values(self, row):
        """
        Cleans the key/value pairs.
        :param row:
        :return: the updated row
        """
        key_1, value_1 = self.clean_key_value(row['key_value_1'])
        key_2, value_2 = self.clean_key_value(row['key_value_2'])
        key_3, value_3 = self.clean_key_value(row['key_value_3'])

        event_type = row['event_type']
        if event_type == 'NOTES':
            row['content'] = value_2
            if value_1:
                prefix = '%s: %s\n' % (key_1, value_1)
                row['content'] = self.clean_append(prefix, row['content'])
            if value_3:
                prefix = '%s: %s\n' % (key_3, value_3)
                row['content'] = self.clean_append(prefix, row['content'])
            if value_1 and value_1 == 'TRASH':
                self.add_tag(row, 'Trash')
        elif event_type == 'SAMPLE':
            row['content'] = '%s: %s\n%s: %s\n %s' % (key_1, value_1, key_2, value_2, value_3)
            self.add_tag(row, 'Sample')
        elif event_type == 'DIVESTATUS':
            row['content'] = value_1
            self.add_tag(row, 'DiveStatus')
        elif event_type == 'OBJECTIVE':
            row['content'] = value_1
            self.add_tag(row, 'Objective')
        elif event_type == 'ENGINEERING':
            row['content'] = '%s: %s\n%s: %s\n %s' % (key_1, value_1, key_2, value_2, value_3)
            self.add_tag(row, 'Engineering')
        elif event_type == 'AUDIOVIDEO':
            key_4, value_4 = self.clean_key_value(row['key_value_4'])
            row['content'] = '%s: %s\n%s: %s\n %s' % (key_2, value_2, key_4, value_4, value_1)
            self.add_tag(row, 'AudioVideo')
        elif event_type == 'DATA':

            key_4, value_4 = self.clean_key_value(row['key_value_4'])
            key_5, value_5 = self.clean_key_value(row['key_value_5'])
            key_6, value_6 = self.clean_key_value(row['key_value_6'])
            key_7, value_7 = self.clean_key_value(row['key_value_7'])

            content = self.append_key_value(None, key_1, value_1)
            content = self.append_key_value(None, key_2, value_2)
            content = self.append_key_value(None, key_3, value_3)
            content = self.append_key_value(None, key_4, value_4)
            content = self.append_key_value(None, key_5, value_5)
            content = self.append_key_value(None, key_6, value_6)
            content = self.append_key_value(None, key_7, value_7)
            row['content'] = content
            self.add_tag(row, 'MultibeamLine')

        else:
            print '*** UNKONWN EVENT TYPE ** %s' % event_type

        self.add_tag(row, 'EventLog')

        del row['key_value_1']
        del row['key_value_2']
        del row['key_value_3']
        del row['key_value_4']
        del row['key_value_5']
        del row['key_value_6']
        del row['key_value_7']
        del row['event_type']

        return row

    def add_tag(self, row, tag_key):
        """
        Looks up the correct tag based on the row, and appends it to the list of tags
        :param row:
        :return: the updated row
        """
        if 'tag' not in row:
            row['tag'] = []
        if tag_key not in row['tag']:
            row['tag'].append(tag_key)
        return row

    def load_csv(self):
        """
        Load the CSV file according to the self.configuration, and store the values in the database using the
        Django ORM.
        Warning: the model's save method will not be called as we are using bulk_create.
        :return: the newly created models, which may be an empty list
        """

        the_model = LocatedNote
        new_models = []
        rows = []
        note_tags = []

        try:
            self.reset_csv()
            for row in self.csv_reader:
                row = self.update_row(row)
                if row:
                    new_note_tags = row['tag']
                    note_tags.append(new_note_tags)
                    del row['tag']
                    rows.append(row)
                    if not self.replace:
                        new_note = the_model(**row)
                        new_note.save()
                        new_note.tags.add(*(new_note_tags))
                        # new_models.append(the_model(**row))
            if not self.replace:
                pass
                # the_model.objects.bulk_create(new_models)
                # for i, note in enumerate(new_models):
                    # tn = TaggedNote(tag=tags[i], content_object=note)
                    # tagged_notes.append(tn)
                # TaggedNote.objects.bulk_create(tagged_notes)
            else:
                self.update_stored_data(the_model, rows)
                #TODO what do we do with the tagged notes?
            self.handle_last_row(row)
        finally:
            self.csv_file.close()
        return new_models

