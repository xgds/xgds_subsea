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
from xgds_core.models import Flight, GroupFlight, Vehicle
from xgds_core.flightUtils import getFlight
from geocamTrack.utils import getClosestPosition

from csv import DictReader
import sys
import re
import datetime
from dateutil.parser import parse as dateparser
import pytz


def importDiveStats(filename):
    """
    Import OET dive stats from a CSV file and write them to the database
    :param filename: the name of the CSV file
    :return: the number of dives imported
    """
    num_imported = 0
    num_rejected_exists = 0

    vehicles = []
    vehicles.append(Vehicle.objects.filter(name='Hercules')[0])
    vehicles.append(Vehicle.objects.filter(name='Argus')[0])
    vehicles.append(Vehicle.objects.filter(name='Ship')[0])

    reader = DictReader(open(filename,'r'),delimiter='\t')
    for row in reader:
        # current, dive, site, inwatertime, inwaternav, ondecktime, ondecknav,
        # onbottomtime, onnav, ondepth, offbottomtime, offnav, offdepth,
        # hercmaxdepth, hercavgdepth, argusmaxdepth, argusavgdepth,
        # totaltime(hours), bottomtime(hours), sampleIDs(range)

        start_time = dateparser(row['inwatertime']).replace(tzinfo=pytz.UTC)
        end_time = dateparser(row['ondecktime']).replace(tzinfo=pytz.UTC)

        # Check for existing database entries with this same instrument and acquisition time
        existingFlights = Flight.objects.filter(
                start_time=start_time, end_time=end_time)

        if len(existingFlights)>0:
            print 'This flight exists:'
            for f in existingFlights:
                print '    %s' % f

        groupFlight = GroupFlight()
        groupFlight.name = row['dive']
        # Pack everything from dive stats into the extras field
        for k, v in row.iteritems():
            groupFlight.extras[k] = v
        groupFlight.save()
        print 'created %s' % groupFlight
        num_imported += 1

        for vehicle in vehicles:
            f = Flight()
            f.name = '%s %s' % (vehicle.name, row['dive'])
            f.vehicle = vehicle
            f.start_time = start_time
            f.end_time = end_time
            # Pack everything from dive stats into the extras field
            for k,v in row.iteritems():
                f.extras[k] = v
            f.group = groupFlight
            f.save()
            print 'created %s' % f
            num_imported += 1

    return num_imported

if __name__=='__main__':
    parser = optparse.OptionParser('usage: %prog')
    parser.add_option('-c', '--cruise', help='name of the cruise containing these dives')

    opts,args = parser.parse_args()
    stats_file = args[0]
    importDiveStats(stats_file)
