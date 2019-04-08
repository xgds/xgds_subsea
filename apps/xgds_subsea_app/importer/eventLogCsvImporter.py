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
import traceback
import re
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from geocamUtil.UserUtil import getUserByUsername, getUserByNames, create_user
from geocamUtil.models import SiteFrame
from xgds_core.models import Condition, ConditionHistory, ConditionStatus
from xgds_core.importer import csvImporter
from xgds_core.flightUtils import lookup_flight
from xgds_notes2.models import LocatedNote, HierarchichalTag, TaggedNote, Role, Location
from xgds_map_server.models import Place
from xgds_sample.models import Sample, SampleType, Label


def safe_delete_key(dictionary, key):
    """
    Safely delete a key from a dictionary only if it exists
    :param dictionary: the dictionary
    :param key: the key to delete
    :return: the dictionary
    """
    try:
        del dictionary[key]
    except:
        pass
    return dictionary


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
    if '' in row:
        del row['']
    return row


def append_key_value(content, key, value):
    """
    Safely append the key/value as a separate line to the content
    :param content:
    :param key:
    :param value:
    :return: new content
    """
    if key and value:
        if content:
            return '%s\n%s: %s' % (content, key, value)
        return '%s: %s' % (key, value)
    return content


def add_notes_tag(row, value):
    """
    Appends the correct tag value to the row
    :param row:
    :param value:
    :return: True if added, False otherwise, "NO VALUE" if no value
    """
    if not value:
        return "NO VALUE"
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
    elif 'Laser Mapping' in value:
        add_tag(row, 'LaserMapping')
    elif 'Other' in value:
        add_tag(row, 'Other')
    else:
        return False
    return True


def add_sample_type_tag(row, value):
    """
    Add the sample specific type tags
    :param row:
    :param value:
    :return: True if added, False otherwise, "NO VALUE" if no value
    """
    if not value:
        return "NO VALUE"
    lower_value = value.lower()
    if 'supr' in lower_value:
        if '1' in lower_value:
            add_tag(row, 'SUPR-1')
        elif '2' in lower_value:
            add_tag(row, 'SUPR-2')
    elif 'igt' in lower_value:
        add_tag(row, 'IGT')
    elif 'rovg' in lower_value:
        add_tag(row, 'ROVGrab')
    elif 'rovpc' in lower_value:
        add_tag(row, 'PushCore')
    elif 'niskin' in lower_value:
        add_tag(row, 'Niskin')
    elif 'scoop' in lower_value:
        add_tag(row, 'Scoop')
    else:
        return False
    return True


def add_divestatus_tag(row, value):
    """
    Add the divestatus specific type tags
    :param row:
    :param value:
    :return: True if added, False otherwise, "NO VALUE" if no value
    """
    if not value:
        return "NO VALUE"
    if 'onbottom' in value:
        add_tag(row, 'OnBottom')
    elif 'offbottom' in value:
        add_tag(row, 'OffBottom')
    elif 'inwater' in value:
        add_tag(row, 'InWater')
    elif 'ondeck' in value:
        add_tag(row, 'OnDeck')
    else:
        return False
    return True


def add_audiovideo_rating_tag(row, value):
    """
    Add the rating tags for audiovideo
    :param row:
    :param value:
    :return: True if valid tag was made, False otherwise, "NO VALUE" if no value
    """
    if not value:
        return "NO VALUE"
    try:
        int_val = int(value)
        if str(int_val) != str(value):
            return False

        if 0 <= int_val <= 5:
            add_tag(row, 'Rating' + str(int_val))
            return True
        else:
            return False
    except:
        return False


def add_timing_or_data_tag(row, value):
    """
    Add tags for timing (start/end/pause/restart etc) or data (average, min, max)
    :param row:
    :param value:
    :return: True if tag added, False otherwise, "NO VALUE" if no value
    """
    if not value:
        return "NO VALUE"
    lower_value = value.lower()
    if 'min' in lower_value:
        add_tag(row, 'Min')
    elif 'max' in lower_value:
        add_tag(row, 'Max')
    elif 'avg' in lower_value:
        add_tag(row, 'Average')
    elif 'average' in lower_value:
        add_tag(row, 'Average')
    elif 'end' in lower_value:
        add_tag(row, 'End')
    elif 'start' in lower_value:
        if 'restart' in lower_value:
            add_tag(row, 'Resume')
        else:
            add_tag(row, 'Start')
    elif 'pause' in lower_value:
        add_tag(row, 'Pause')
    elif 'resume' in lower_value:
        add_tag(row, 'Resume')
    elif 'stop' in lower_value:
        add_tag(row, 'Stop')
    else:
        return False
    return True


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
    It will also do sample creation, as samples are recorded through the event log.
    """

    def __init__(self, yaml_file_path, csv_file_path, vehicle_name=None, flight_name=None, timezone_name='UTC',
                 defaults=None, force=False, replace=False, skip_bad=False):

        self.datalogger_user = getUserByUsername('datalogger')
        self.navigator_user = getUserByUsername('navigator')
        self.scf_user = getUserByUsername('scicommfellow')
        self.herc_user = getUserByUsername('herc')
        self.importer_user = getUserByUsername('importer')

        self.roles = {'NAVIGATOR': Role.objects.get(value='NAVIGATOR'),
                      'SCF': Role.objects.get(value='SCIENCE_COMMUNICATION_FELLOW'),
                      'DATA_LOGGER': Role.objects.get(value='DATA_LOGGER')}

        self.ship_location = Location.objects.get(value='SHIP')

        self.sample_content_type = ContentType.objects.get_for_model(Sample)

        self.condition_started = ConditionStatus.objects.get(value='started')
        self.condition_completed = ConditionStatus.objects.get(value='completed')
        super(EventLogCsvImporter, self).__init__(yaml_file_path, csv_file_path, vehicle_name, flight_name,
                                                  timezone_name, defaults, force, replace, skip_bad)

    def check_data_exists(self, row):
        """
        See if there is already identical data
        :param row: typically the first row
        :return: True if it already exists, false otherwise
        """
        row = self.update_row(row)
        row_copy = row.copy()
        safe_delete_key(row, 'tag')
        if 'condition_data' in row_copy:
            safe_delete_key(row_copy, 'condition_data')
            safe_delete_key(row_copy, 'condition_history_data')
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

        result = self.clean_site(result)
        result = self.clean_author(result)
        result = self.clean_key_values(result)
        if result:
            result = remove_empty_keys(result)
            result['location'] = self.ship_location
        return result

    def clean_site(self, row):
        """
        Updates the row based on the site
        :param row:
        :return:
        """
        if 'site' in row:
            key, site_string = clean_key_value(row['site'])
            if site_string:
                site_string = site_string.replace('_',' ')
                try:
                    place = Place.objects.get(name=site_string)
                except:
                    # create a new place
                    place = Place(name=site_string, creator=self.importer_user,
                                  creation_time=timezone.now(),
                                  region=SiteFrame.objects.get(pk=settings.XGDS_CURRENT_SITEFRAME_ID))
                    Place.add_root(instance=place)
                row['place'] = place
            safe_delete_key(row, 'site')
        return row

    def clean_author(self, row):
        """
        Updates the row by looking up the correct author id by the name
        Also figure out the role based on the author.  Defaults to DATA_LOGGER
        :param row:
        :return: the updated row
        """
        if 'author_name' in row:
            author_name = row['author_name']
            lower_name = author_name.lower()
            if author_name.lower() == 'nav' or lower_name == 'navigator' or lower_name == 'navigation':
                row['role'] = self.roles['NAVIGATOR']
                row['author'] = self.navigator_user
            elif author_name.lower() == 'default_scf_user':
                row['role'] = self.roles['SCF']
                row['author'] = self.scf_user
            else:
                row['role'] = self.roles['DATA_LOGGER']
                splits = author_name.split('_')
                if len(splits) == 2:
                    try:
                        row['author'] = getUserByNames(splits[0], splits[1])
                    except:
                        # TODO This happend for NA100 due to errors in cruise-record.xml
                        print 'COULD NOT FIND USER FOR %s' % author_name
                        print 'creating new user'
                        row['author'] = create_user(splits[0], splits[1])

        if 'author' not in row:
            row['author'] = self.datalogger_user

        if 'author_name' in row:
            safe_delete_key(row, 'author_name')
        else:
            print "*** THIS ROW HAS NO AUTHOR FIELD **"
            print row

        return row

    def clean_flight(self, row, vehicle_name=None):
        """
        Updates the row by looking up the correct flight id by the name.
        Hardcoding to Hercules vehicle
        :param row: the dict of the row we are working on
        :param vehicle_name: the name of the vehicle
        :return: the updated row
        """
        if not vehicle_name and 'vehicle_name' in row:
            key, rvn = clean_key_value(row['vehicle_name'])
            if not rvn:
                print 'NULL VEHICLE, DEFAULTING TO HERCULES %s' % rvn
            else:
                if rvn == 'Argus':
                    vehicle_name = rvn
                elif 'Herc' in rvn:
                    vehicle_name = 'Hercules'
                else:
                    print 'INVALID VEHICLE, DEFAULTING TO HERCULES %s' % rvn
            if not vehicle_name:
                vehicle_name = self.vehicle.name
        safe_delete_key(row, 'vehicle_name')

        if 'group_flight_name' in row:
            if 'flight' not in row or row['flight'] is None:
                flight_name = row['group_flight_name'] + '_' + vehicle_name
                row['flight'] = lookup_flight(flight_name)
                if row['flight']:
                    print ('looked up flight %d %s' % (row['flight'].id, row['flight'].name))
            safe_delete_key(row, 'group_flight_name')
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
        key_3 = None
        value_3 = None
        if 'key_value_3' in row:
            key_3, value_3 = clean_key_value(row['key_value_3'])

        event_type = row['event_type']
        if event_type == 'NOTES':
            row['content'] = value_2
            if value_3:
                td_tag_added = add_timing_or_data_tag(row, value_3)
                if td_tag_added and 'Max' in row['tag']:
                    # the max value is stored in the marker field but it is not really a marker
                    prefix = '%s\n' % value_3
                else:
                    prefix = '%s: %s\n' % (key_3, value_3)
                row['content'] = clean_append(prefix, row['content'])
            tag_added = add_notes_tag(row, value_1)
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_1, str(row))
                row['content'] = '%s\n%s: %s' % (row['content'], key_1, value_1)
        elif event_type == 'SAMPLE':
            tag_added = add_sample_type_tag(row, value_2)
            sample_data = self.populate_sample_data(row, value_1, value_3)
            if sample_data:
                row['sample_data'] = sample_data
            row['content'] = '%s: %s\n%s' % (key_1, value_1, value_3)
            add_tag(row, 'Sample')
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_2, str(row))
                row['content'] = '%s\n%s: %s' % (row['content'], key_2, value_2)
            condition, condition_history = self.populate_condition_data(row, value_1.replace(' ', '-'),
                                                                        self.condition_completed)
            row['condition_data'] = condition
            row['condition_history_data'] = condition_history
        elif event_type == 'DIVESTATUS':
            row['content'] = value_1
            add_tag(row, 'DiveStatus')
            tag_added = add_divestatus_tag(row, value_1)
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_1, str(row))
                row['content'] = '%s\n%s: %s' % (row['content'], key_1, value_1)

            last_tag = row['tag'][-1]
            status = self.condition_completed
            if last_tag == 'OnBottom' or last_tag == 'InWater':
                status = self.condition_started
            condition, condition_history = self.populate_condition_data(row, last_tag, status)
            row['condition_data'] = condition
            row['condition_history_data'] = condition_history
        elif event_type == 'OBJECTIVE':
            row['content'] = value_1
            add_tag(row, 'Objective')
        elif event_type == 'ENGEVENT':
            row['content'] = value_3
            add_tag(row, 'Engineering')
            tag_added = add_tag(row, value_1, capitalize=True)
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_1, str(row))
                row['content'] = '%s\n%s: %s' % (row['content'], key_1, value_1)
            tag_added = add_tag(row, value_2, capitalize=True)
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_2, str(row))
                row['content'] = '%s\n%s: %s' % (row['content'], key_2, value_2)
        elif event_type == 'AUDIOVIDEO':
            if value_3:
                if 'Herc/Argus' not in value_3:
                    if 'argus' in value_3.lower():
                        row = self.clean_flight(row, 'Argus')

            key_4, value_4 = clean_key_value(row['key_value_4'])
            row['content'] = '%s: %s\n %s' % (key_2, value_2, value_1)
            add_tag(row, 'AudioVideo')
            tag_added = add_audiovideo_rating_tag(row, value_4)
            if not tag_added:
                print 'MATCHING TAG NOT FOUND FOR %s IN %s' % (value_4, str(row))
                row['content'] = '%s\nRATING: %s' % (row['content'], value_4)
        elif event_type == 'DATA':
            key_4, value_4 = clean_key_value(row['key_value_4'])
            key_5, value_5 = clean_key_value(row['key_value_5'])
            key_6, value_6 = clean_key_value(row['key_value_6'])
            key_7, value_7 = clean_key_value(row['key_value_7'])
            key_8, value_8 = clean_key_value(row['key_value_8'])

            if row['task_type'] == 'MULTIBEAMLINE':
                add_tag(row, 'MultibeamLine')
            elif row['task_type'] == 'PROFILES':
                add_tag(row, 'Profiles')
            else:
                print 'UNKOWN DATA TASK TYPE %s: %s' % (row['task_type'], str(row))
            content = append_key_value(None, key_1, value_1)
            content = append_key_value(content, key_2, value_2)
            content = append_key_value(content, key_3, value_3)
            content = append_key_value(content, key_4, value_4)
            content = append_key_value(content, key_5, value_5)
            content = append_key_value(content, key_6, value_6)
            content = append_key_value(content, key_7, value_7)
            content = append_key_value(content, key_8, value_8)
            row['content'] = content

        else:
            print '*** UNKONWN EVENT TYPE ** %s' % event_type

        row = self.clean_flight(row)
        if 'condition_data' in row:
            if 'flight' in row:
                row['condition_data']['flight'] = row['flight']

        if 'tag' in row and not row['tag']:
            safe_delete_key(row, 'tag')

        safe_delete_key(row, 'key_value_1')
        safe_delete_key(row, 'key_value_2')
        safe_delete_key(row, 'key_value_3')
        safe_delete_key(row, 'key_value_4')
        safe_delete_key(row, 'key_value_5')
        safe_delete_key(row, 'key_value_6')
        safe_delete_key(row, 'key_value_7')
        safe_delete_key(row, 'key_value_8')
        safe_delete_key(row, 'event_type')
        safe_delete_key(row, 'task_type')
        return row

    def populate_condition_data(self, row, name, status):
        """
        Create metadata for storing condition with condition history for specific events, including:
        DiveStatus
        Sample
        :param row:
        :return: the condition and condition history dictionaries as a tuple
        """
        now = timezone.now()
        condition_data = {'source': 'Event Log Import',
                          'start_time': row['event_time'],
                          'end_time': row['event_time'],
                          'name': name
                          }
        if 'flight' in row and row['flight'] is not None:
            condition_data['flight'] = row['flight']

        content_dict = {"content": "%s" % row["content"]}
        condition_history_data = {'source_time': row['event_time'],
                                  'creation_time': now,
                                  'status': status,
                                  'jsonData': json.dumps(content_dict)
                                  }

        return condition_data, condition_history_data

    def populate_sample_data(self, row, name, description):

        """
        Since samples are created in the event log and we have already parsed the information, 
        we will create a dictionary with information to create the sample here
        :return: the dictionary of sample data
        """
        found_sample = None
        # we have found cases where samples had bad names with underscores or space
        name = name.replace(' ', '-')
        name = name.replace('_', '-')
        try:
            found_sample = Sample.objects.get(name=name)
            if not self.replace:
                # we want to continue
                print 'Sample already exists and replace not specified %s' % name
                return None
        except ObjectDoesNotExist:
            pass
        sample_type = None
        if 'tag' in row and row['tag']:
            try:
                sample_type = SampleType.objects.get(value=row['tag'][0])
            except:
                print 'sample type %s NOT FOUND' % row['tag'][0]
        else:
            print 'SAVING SAMPLE WITH NO TYPE %s' % name
        right_now = timezone.now()

        place = None
        if 'place' in row:
            place = row['place']
        sample_data = {'name': name,
                       'sample_type': sample_type,
                       'place': place,
                       'creator': row['author'],
                       'collector': self.herc_user,
                       'collection_time': row['event_time'],
                       'collection_timezone': settings.TIME_ZONE,
                       'modification_time': right_now,
                       'description': description,
                       }
        if not found_sample:
            name_match = re.search('NA(\d*)[-|\s](\d*)', name)
            sample_label_string = ""
            sample_label_number = None
            for n in name_match.groups():
                sample_label_string += n
            if sample_label_string:
                sample_label_number = int(sample_label_string)
            sample_data['sample_label_number'] = sample_label_number
        else:
            sample_data['sample_label_number'] = found_sample.label.number

        return sample_data

    def build_models(self, row):
        """
        Build the models based on the cleaned up row
        :return: list of models of varying types
        """
        if not row:
            return None

        the_model = LocatedNote
        new_models = []
        new_note_tags = None

        # Create the note and the tags.  Because the tags cannot be created until the note exists,
        # we have to do this one at a time.
        try:
            has_tag = False
            found_position_id = None
            sample = None
            if 'tag' in row:
                has_tag = True
                new_note_tags = row['tag']
                safe_delete_key(row, 'tag')
            if 'sample_data' in row:
                # This is a sample; create it and set the foreign key
                sample_data = row['sample_data']
                safe_delete_key(row, 'sample_data')
                label, created = Label.objects.get_or_create(number=sample_data['sample_label_number'])
                safe_delete_key(sample_data, 'sample_label_number')
                sample_data['label'] = label
                sample_data['flight'] = row['flight']
                if created:
                    sample_data['creation_time'] = sample_data['modification_time']
                    # assume the time of the sample will not change; look up position here
                    sample_data = csvImporter.lookup_position(sample_data, timestamp_key='collection_time',
                                                              position_id_key='track_position_id',
                                                              retries=3)
                    if 'track_position_id' in sample_data:
                        found_position_id = sample_data['track_position_id']
                        row['position_id'] = found_position_id
                        row['position_found'] = True
                    else:
                        row['position_found'] = False

                try:
                    sample = Sample.objects.create(**sample_data)
                    new_models.append(sample)
                except Exception as e:
                    # This sample already existed, update it instead.
                    sample_filter = Sample.objects.filter(name=sample_data['name'], label=label)
                    sample_filter.update(**sample_data)
                    sample = sample_filter[0]

                # set the generic foreign key on the note
                if sample:
                    row['content_type'] = self.sample_content_type
                    row['object_id'] = sample.pk
            if 'condition_data' in row:
                # this has a condition.
                # If it was not a sample, see if it already exists.
                skip = False
                if not sample:
                    found_conditions = Condition.objects.filter(flight=row['flight'],
                                                                name=row['condition_data']['name'])
                    if found_conditions:
                        skip = True

                if not skip:
                    condition = Condition.objects.create(**row['condition_data'])
                    new_models.append(condition)
                    condition_history_data = row['condition_history_data']
                    condition_history_data['condition'] = condition
                    condition_history = ConditionHistory.objects.create(**condition_history_data)
                    new_models.append(condition_history)

                    # update prior condition to complete it if it is a dive status
                    update = False
                    filter_name = None
                    if condition.name == 'OnDeck':
                        filter_name = 'InWater'
                    elif condition.name == 'OffBottom':
                        filter_name = 'OnBottom'
                    if filter_name:
                        found_conditions = Condition.objects.filter(flight=condition.flight, name=filter_name)
                        if found_conditions:
                            last_condition = found_conditions.last()
                            last_condition_history = last_condition.getHistory().last()
                            if last_condition_history.status != self.condition_completed:
                                condition_history_data['condition'] = last_condition
                                update = True
                        if update:
                            condition_history_data['status'] = self.condition_completed
                            condition_history2 = ConditionHistory.objects.create(**condition_history_data)
                            new_models.append(condition_history2)

                safe_delete_key(row, 'condition_data')
                safe_delete_key(row, 'condition_history_data')

            if not found_position_id:
                row = csvImporter.lookup_position(row, timestamp_key='event_time',
                                                  position_id_key='position_id',
                                                  position_found_key='position_found',
                                                  retries=3)

            # this should really never happen!!!
            if 'author' not in row or not row['author']:
                print('NO AUTHOR IN ROW, defaulting to datalogger')
                print(row)
                row['author'] = self.datalogger_user

            if self.replace:
                new_note, note_created = the_model.objects.update_or_create(**row)
            else:
                new_note = the_model.objects.create(**row)

            if has_tag:
                new_note.tags.clear()
                new_note.tags.add(*new_note_tags)
            new_models.append(new_note)
        except Exception as e:
            traceback.print_exc()
            print new_note_tags
            print row
            e.message = str(row) + e.message
            raise e

        return new_models

    def load_csv(self):
        """
        Load the CSV file according to the self.configuration, and store the values in the database using the
        Django ORM.
        Warning: the model's save method will not be called as we are using bulk_create.
        :return: the newly created models, which may be an empty list
        """

        new_models = []
        try:
            self.reset_csv()
            for row in self.csv_reader:
                row = self.update_row(row)
                if row:
                    models = self.build_models(row)
                    if models:
                        new_models.extend(models)
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
                has_tag = False
                if 'tag' in row:
                    has_tag = True
                    new_note_tags = row['tag']
                    safe_delete_key(row, 'tag')
                for key, value in row.iteritems():
                    setattr(item, key, value)
                item.tags.clear()
                if has_tag:
                    item.tags.add(*new_note_tags)

                print 'UPDATED: %s ' % str(item)
                item.save()


