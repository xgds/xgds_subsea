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

import re

import pytz
from datetime import datetime
from dateutil.parser import parse as dateparser

from geocamUtil.UserUtil import getUserByUsername, getUserByNames, create_user
from xgds_core.importer import csvImporter
from xgds_core.flightUtils import getFlight, get_default_vehicle


def clean_author(row):
    """
    Updates the row by looking up the correct author id by the name
    Also figure out the role based on the author.  Defaults to DATA_LOGGER
    :param row:
    :return: the updated row
    """
    if 'author_name' not in row:
        raise KeyError("Row does not contain author_name %s" % str(row))

    author_name = row['author_name']
    if not author_name:
        raise AssertionError("Author name is empty %s" % str(row))

    author = None

    split_name = re.sub('([a-z])([A-Z])', r'\1 \2', author_name).split()
    if len(split_name) == 1:
        last_name = ""
    else:
        last_name = "".join(split_name[1:])

    # try the split name
    if len(split_name) > 1:
        author = getUserByNames(split_name[0], last_name)

    if not author:
        # try the username
        author = getUserByUsername(author_name)

    if not author:
        author = create_user(split_name[0], last_name)

    if author:
        row['author'] = author
        del row['author_name']
    else:
        raise "Problem creating user for %s" % author_name

    return row


class SciChatCsvImporter(csvImporter.CsvImporter):
    """
    Utilities for loading scichat files from files such as <cruise>/processed/eventlog/by-day/all_chatlog_<DIVE>.txt
    This will create messages with references to the correct users, positions and flights.
    """

    def __init__(self, yaml_file_path, csv_file_path, vehicle_name=None, flight_name=None, timezone_name='UTC',
                 defaults=None, force=False, replace=False, skip_bad=False):
        self.hercules = get_default_vehicle()
        super(SciChatCsvImporter, self).__init__(yaml_file_path, csv_file_path, vehicle_name, flight_name,
                                                  timezone_name, defaults, force, replace, skip_bad)

    def get_time(self, row, field_name=None):
        """
        The data we get over UDP is inconsistent with the data we get from the import.
        It will come in in two fields, event_date and event_time
        :param row:
        :param field_name:
        :return:
        """

        if 'conglomerate' in row and 'event_time' in row:
            # CHAT 2019/06/04 17:15:58.256 SCIENCECHAT 1559668554
            conglomerate = row['conglomerate']
            splits = conglomerate.split(' ')
            date_value = splits[1]
            time_value = row['event_time']
            del row['conglomerate']
            the_time = dateparser(date_value + ' ' + time_value)
            if not the_time.tzinfo or the_time.tzinfo.utcoffset(the_time) is None:
                the_time = self.timezone.localize(the_time)
            the_time = the_time.astimezone(pytz.utc)
            return the_time

        return super(SciChatCsvImporter, self).get_time(row, field_name)

    def update_row(self, row):
        """
        Update the row from the self.config
        :param row: the loaded row
        :return: the updated row, with timestamps and defaults
        """
        print(row)
        result = super(SciChatCsvImporter, self).update_row(row)
        result = clean_author(result)
        result = self.clean_flight(result)
        result = csvImporter.lookup_position(result, timestamp_key='event_time', position_found_key='position_found',
                                             retries=3)
        return result

    def clean_flight(self, row):
        """
        Updates the row by looking up the correct flight id by the name.
        Hardcoding to Hercules vehicle
        :param row:
        :return: the updated row
        """
        row['flight'] = getFlight(row['event_time'], self.hercules)
        return row

