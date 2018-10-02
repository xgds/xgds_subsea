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

from geocamUtil.UserUtil import getUserByUsername, getUserByNames, create_user
from geocamTrack.utils import getClosestPosition
from xgds_core.importer import csvImporter
from xgds_core.FlightUtils import getFlight, get_default_vehicle


class SciChatCsvImporter(csvImporter.CsvImporter):
    """
    Utilities for loading scichat files from files such as <cruise>/processed/eventlog/by-day/all_chatlog_<DIVE>.txt
    This will create messages with references to the correct users, positions and flights.
    """

    hercules = get_default_vehicle()

    def update_row(self, row):
        """
        Update the row from the self.config
        :param row: the loaded row
        :return: the updated row, with timestamps and defaults
        """
        result = super(SciChatCsvImporter, self).update_row(row)
        result = self.clean_author(result)
        result = self.clean_flight(result)
        result = self.lookup_position(result)
        return result

    def lookup_position(self, row):
        track=None
        if row['flight']:
            track = row['flight'].track
        found_position = getClosestPosition(track=track,
                                            timestamp=row['event_time'])

        if found_position:
            row['position_id'] = found_position.id
        else:
            print 'NO POSITION FOUND FOR TIME %s' % str(row['event_time'])
        return row

    def clean_author(self, row):
        """
        Updates the row by looking up the correct author id by the name
        Also figure out the role based on the author.  Defaults to DATA_LOGGER
        :param row:
        :return: the updated row
        """
        author_name = row['author_name']
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

    def clean_flight(self, row):
        """
        Updates the row by looking up the correct flight id by the name.
        Hardcoding to Hercules vehicle
        :param row:
        :return: the updated row
        """
        row['flight'] = getFlight(row['event_time'], self.hercules)
        return row

