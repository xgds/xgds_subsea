#!/usr/bin/env python
#  __BEGIN_LICENSE__
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

import optparse

import django
django.setup()

from geocamUtil.xml2json import xml2struct
from geocamUtil.UserUtil import create_user


def create_users(xml_filename, test_mode=False, verbose=False):
    """
    Import OET cruise record XML file and create django auth users from the list of participants
    :param filename: the name of the XML file
    :return: the number of users created
    """
    num_created = 0

    cruise_record = xml2struct(xml_filename)
    participant_list = cruise_record['oet:oetcruise']['r2r:cruise']['r2r:cruiseParticipants']['r2r:cruiseParticipant']
    names = [participant['r2r:cruiseParticipantName']['text'] for participant in participant_list]
    for name in names:
        split_name = name.split()
        first_name = split_name[0]
        last_name = "".join(split_name[1:])

        new_user = create_user(first_name, last_name, save=not test_mode, verbose=verbose)
        if new_user:
            print 'Created user', new_user.username, '(%s)' % name
            num_created += 1

    return num_created


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-t', '--test', action="store_true", default=False, help='run in test mode, do not create users')
    parser.add_option('-v', '--verbose', action="store_true", default=False, help='verbose mode')

    opts, args = parser.parse_args()
    cruise_record = args[0]
    created = create_users(cruise_record, test_mode=opts.test, verbose=opts.verbose)
    if opts.verbose:
        print 'Created %d users' % created
