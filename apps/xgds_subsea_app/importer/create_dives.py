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
from xgds_core.models import Flight, GroupFlight, Vehicle

from csv import DictReader
from dateutil.parser import parse as dateparser
import pytz


def create_dives(filename):
    """
    Import OET dive stats from a CSV file and write them to the database
    :param filename: the name of the CSV file
    :return: the number of dives imported
    """
    num_created = 0

    vehicles = [Vehicle.objects.get(name='Hercules'),
                Vehicle.objects.get(name='Argus'),
                Vehicle.objects.get(name='Nautilus')]

    reader = DictReader(open(filename, 'r'), delimiter='\t')
    for row in reader:
        start_time = dateparser(row['inwatertime']).replace(tzinfo=pytz.UTC)
        end_time = dateparser(row['ondecktime']).replace(tzinfo=pytz.UTC)

        # Check for existing database entries with this same instrument and acquisition time
        existing_group_flights = GroupFlight.objects.filter(
                name=row['dive'])
        existing_flights = Flight.objects.filter(
                start_time=start_time, end_time=end_time)

        if len(existing_flights) > 0 or len(existing_group_flights) > 0:
            print 'This flight exists:'
            for g in existing_group_flights:
                print '    %s' % g
            for f in existing_flights:
                print '    %s' % f
            continue

        group_flight = GroupFlight()
        group_flight.name = row['dive']
        # Pack everything from dive stats into the extras field
        for k, v in row.iteritems():
            if not v or not k:
                pass
            if len(k) == 0:
                pass
            if k == "":
                pass
            if k.startswith("##"):  # we know the ## bla is the name of the cruise
                k = "cruise"

            # further sanitize the keys, some of them have parens in them
            if '(' in k:
                k = k[0:k.index('(')]
            group_flight.extras[k] = v

        group_flight.save()
        # print 'created %s' % groupFlight
        num_created += 1

        for vehicle in vehicles:
            f = Flight()
            f.name = '%s_%s' % (row['dive'], vehicle.name)
            f.vehicle = vehicle
            f.start_time = start_time
            f.end_time = end_time
            # Pack everything from dive stats into the extras field
            # for k, v in row.iteritems():
            #     f.extras[k] = v
            # TC: I don't think we need the above because it's in the group flight
            f.group = group_flight
            f.save()
            # print 'created %s' % f
            num_created += 1

    return num_created


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-c', '--cruise', help='name of the cruise containing these dives')

    opts, args = parser.parse_args()
    stats_file = args[0]
    created = create_dives(stats_file)
    print 'Created %d dives and group dives' % created
