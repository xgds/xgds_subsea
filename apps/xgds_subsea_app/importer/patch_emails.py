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
import csv

from validate_email import validate_email

import django
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


def patch_emails(csv_filename, verbose=False):
    """
    patch existing users with email addresses
    :param csv_filename: a csv input file with username email address
    :param verbose: true to print details
    :return: (# patched, # skipped)
    """
    patched = 0
    skipped = 0

    with open(csv_filename, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) > 1:
                username = row[0]
                email = row[1]
                if validate_email(email):
                    try:
                        found_user = User.objects.get(username=username)
                        found_user.email = email
                        found_user.save()
                        if verbose:
                            print 'Patched %s: %s' % (username, email)
                        patched += 1
                    except ObjectDoesNotExist:
                        skipped += 1
                        if verbose:
                            print 'Could not find username %s' % username
                else:
                    skipped += 1
                    if verbose:
                        print 'Invalid email %s: %s' % (username, email)
            else:
                print 'Require username and email %s' % row
                skipped += 1
    return patched, skipped


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-v', '--verbose', action="store_true", default=False, help='verbose mode')

    opts, args = parser.parse_args()
    if len(args) == 0:
        print 'You must pass full path to csv file as the first argument'
        exit(1)
    csv_filename = args[0]
    patched, skipped = patch_emails(csv_filename, verbose=opts.verbose)
    if opts.verbose:
        print 'Patched %d users email addresses' % patched
        print 'Skipped %d users email addresses' % skipped