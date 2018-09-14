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


def clean_key_value(dictionary):
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


def clean_append(part_1, part_2):
    """
    Safely append 2 parts together, handling None
    :param part_1: 
    :param part_2: 
    :return: 
    """
    if part_1:
        if part_2:
            return part_1 + part_2
        return part_1
    return part_2


def remove_empty_keys(row):
    """
    Remove all unneccessary things from the dictionary
    :param row:
    :return:
    """
    if None in row:
        del row[None]
    return row


def append_key_value(content, key, value):
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


def add_notes_tag(row, value):
    if not value:
        return
    if 'Trash' in value:
        add_tag(row, 'Trash')
    elif 'Biology' in value:
        add_tag(row, 'Biology')
    elif 'Geology' in value:
        add_tag(row, 'Geology')
    elif 'T-ROV' in value:
        add_tag(row, 'TempProbe')
    elif 'T-IGT' in value:
        add_tag(row, 'TempIGT')
    elif 'T-SUPR' in value:
        add_tag(row, 'TempSUPR')


def add_sample_type_tag(row, value):
    """
    Add the sample specific type tags
    :param row:
    :param value:
    :return:
    """
    if not value:
        return
    if 'SUPR' in value:
        add_tag(row, 'SUPR')
    elif 'IGT' in value:
        add_tag(row, 'IGT')
    elif 'ROVG' in value:
        add_tag(row, 'ROVGrab')
    elif 'ROVPC' in value:
        add_tag(row, 'PushCore')
    elif 'Niskin' in value:
        add_tag(row, 'Niskin')


def add_divestatus_tag(row, value):
    """
    Add the divestatus specific type tags
    :param row:
    :param value:
    :return:
    """
    if not value:
        return
    if 'onbottom' in value:
        add_tag(row, 'OnBottom')
    elif 'offbottom' in value:
        add_tag(row, 'OffBottom')
    elif 'inwater' in value:
        add_tag(row, 'InWater')
    elif 'ondeck' in value:
        add_tag(row, 'OnDeck')


def add_audiovideo_rating_tag(row, value):
    """
    Add the rating tags for audiovideo
    TODO figure out what all the ratings can be
    :param row:
    :param value:
    :return:
    """
    if not value:
        return
    add_tag(row, 'Rating' + value)


def add_tag(row, tag_key, capitalize=False):
    """
    Looks up the correct tag based on the row, and appends it to the list of tags
    :param row:
    :param tag_key: the tag key (string of tag) to add
    :param capitalize: True to initial cap the tag key
    :return: the updated row
    """
    if not tag_key:
        return
    if 'tag' not in row:
        row['tag'] = []
    if capitalize:
        tag_key = tag_key.capitalize()
    if tag_key not in row['tag']:
        row['tag'].append(tag_key)
    return row


class EventLogCsvImporter(csvImporter.CsvImporter):
    """
    Utilities for loading event log files from files such as <cruise>/processed/eventlog/by-dive/all_eventlog_<DIVE>.txt
    This will create notes with references to the correct users, roles, locations and tags.
    It will skip sample creation, as samples are recorded separately
    """

    datalogger_user = getUserByUsername('datalogger')
    navigator_user = getUserByUsername('navigator')
    scf_user = getUserByUsername('scf')

    roles = {'NAVIGATOR': Role.objects.get(value='NAVIGATOR'),
             'SCF': Role.objects.get(value='SCIENCE_COMMUNICATION_FELLOW'),
             'DATA_LOGGER': Role.objects.get(value='DATA_LOGGER')}

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
            result = remove_empty_keys(result)
            result['location'] = self.ship_location

        return result

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

    def clean_flight(self, row, vehicle_name=None):
        """
        Updates the row by looking up the correct flight id by the name.
        Hardcoding to Hercules vehicle
        :param row:
        :return: the updated row
        """
        if not vehicle_name:
            key, rvn = clean_key_value(row['vehicle_name'])
            if rvn == 'Argus':
                vehicle_name = rvn
            elif 'Herc' in rvn:
                vehicle_name = 'Hercules'
            else:
                print 'INVALID VEHICLE, DEFAULTING TO HERCULES %s' % rvn
            if not vehicle_name:
                vehicle_name = self.vehicle.name
        flight_name = row['group_flight_name'] + '_' + vehicle_name
        row['flight'] = lookup_flight(flight_name)
        del row['group_flight_name']
        del row['vehicle_name']
        return row

    def clean_key_values(self, row):
        """
        Cleans the key/value pairs.
        This is including setting up the note content, tags and flight.
        :param row:
        :return: the updated row
        """
        key_1, value_1 = clean_key_value(row['key_value_1'])
        key_2, value_2 = clean_key_value(row['key_value_2'])
        key_3, value_3 = clean_key_value(row['key_value_3'])

        flight_set = False
        event_type = row['event_type']
        if event_type == 'NOTES':
            row['content'] = value_2
            if value_3:
                prefix = '%s: %s\n' % (key_3, value_3)
                row['content'] = clean_append(prefix, row['content'])
            add_notes_tag(row, value_1)
        elif event_type == 'SAMPLE':
            row['content'] = '%s: %s\n%s' % (key_1, value_1, value_3)
            add_tag(row, 'Sample')
            add_sample_type_tag(row, value_2)
        elif event_type == 'DIVESTATUS':
            row['content'] = value_1
            add_tag(row, 'DiveStatus')
            add_divestatus_tag(row, value_1)
        elif event_type == 'OBJECTIVE':
            row['content'] = value_1
            add_tag(row, 'Objective')
        elif event_type == 'ENGEVENT':
            row['content'] = value_3
            add_tag(row, 'Engineering')
            add_tag(row, value_1, capitalize=True)
            add_tag(row, value_2, capitalize=True)
        elif event_type == 'AUDIOVIDEO':
            if value_3:
                if 'Herc/Argus' not in value_3:
                    if 'argus' in value_3.lower():
                        row = self.clean_flight(row, 'Argus')
                        flight_set = True

            key_4, value_4 = clean_key_value(row['key_value_4'])
            row['content'] = '%s: %s\n %s' % (key_2, value_2, value_1)
            add_tag(row, 'AudioVideo')
            add_audiovideo_rating_tag(row, value_4)
        elif event_type == 'DATA':

            key_4, value_4 = clean_key_value(row['key_value_4'])
            key_5, value_5 = clean_key_value(row['key_value_5'])
            key_6, value_6 = clean_key_value(row['key_value_6'])
            key_7, value_7 = clean_key_value(row['key_value_7'])

            content = append_key_value(None, key_1, value_1)
            content = append_key_value(content, key_2, value_2)
            content = append_key_value(content, key_3, value_3)
            content = append_key_value(content, key_4, value_4)
            content = append_key_value(content, key_5, value_5)
            content = append_key_value(content, key_6, value_6)
            content = append_key_value(content, key_7, value_7)
            row['content'] = content
            add_tag(row, 'MultibeamLine')

        else:
            print '*** UNKONWN EVENT TYPE ** %s' % event_type

        add_tag(row, 'EventLog')
        if not flight_set:
            row = self.clean_flight(row)

        del row['key_value_1']
        del row['key_value_2']
        del row['key_value_3']
        del row['key_value_4']
        del row['key_value_5']
        del row['key_value_6']
        del row['key_value_7']
        del row['event_type']

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

        try:
            self.reset_csv()
            for row in self.csv_reader:
                row = self.update_row(row)
                if row:
                    rows.append(row)
                    if not self.replace:
                        # Create the note and the tags.  Because the tags cannot be created until the note exists,
                        # we have to do this one at a time.
                        new_note_tags = row['tag']
                        del row['tag']
                        new_note = the_model(**row)
                        new_note.save()
                        new_note.tags.add(*new_note_tags)
                        new_models.append(new_note)
            if self.replace:
                self.update_stored_data(the_model, rows)
            self.handle_last_row(row)
        finally:
            self.csv_file.close()
        return new_models

    def update_stored_data(self, the_model, rows):
        """
        # search for matching data based on each row, and update it.
        :param the_model: the model we are working with
        :param rows: the cleaned up rows we are working with
        :return:
        """
        for row in rows:
            filter_dict = {self.config['timefield_default']: row[self.config['timefield_default']]}
            if self.flight:
                filter_dict['flight'] = self.flight

            found = the_model.objects.filter(**filter_dict)
            if found.count() != 1:
                print "ERROR: DID NOT FIND MATCH FOR %s" % str(row[self.config['timefield_default']])
            else:
                item = found[0]
                new_note_tags = row['tag']
                del row['tag']
                for key, value in row.iteritems():
                    setattr(item, key, value)
                item.tags.clear()
                item.tags.add(*new_note_tags)

                print 'UPDATED: %s ' % str(item)
                item.save()


