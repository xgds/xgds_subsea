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
from django.conf import settings
from django.contrib.auth.models import User

import json
from geocamUtil.xml2json import xml2struct

def username_exists(username):
    existing_users = User.objects.filter(username=username)
    return len(existing_users) > 0


def create_users(xml_filename, test=False):
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
        parts = name.split()
        first_name = parts[0]
        last_name = parts[-1]
        # Username is first initial plus last name in lower case
        username = first_name[0].lower() + last_name.lower()
        existing_users = User.objects.filter(first_name=first_name,last_name=last_name)
        if len(existing_users)>0:
            print 'This user already exists:'
            for u in existing_users:
                print '    ', u.username, '(%s)' % name
            continue

        if username_exists(username):
            user_uniquifier = 1
            while username_exists(username):
                print 'Username %s is already in use' % username
                username = first_name[0].lower() + last_name.lower() + '%s' % user_uniquifier
                user_uniquifier += 1

        # Now we should have a unique username and a need to create the user
        new_user = User()
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.username = username
        new_user.password = "*"
        new_user.is_active = False
        new_user.is_superuser = False
        new_user.save()
        print 'Created user', new_user.username, '(%s)' % ' '.join(parts)
        num_created += 1

    return num_created


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-t', '--test', action="store_true", default=False, help='run in test mode, do not create users')

    opts, args = parser.parse_args()
    cruise_record = args[0]
    created = create_users(cruise_record, test=opts.test)
    print 'Created %d users' % created
