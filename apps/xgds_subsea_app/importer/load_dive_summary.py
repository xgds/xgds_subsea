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

"""
Loads the dive summary
Also connects the dive plan
"""
import os
import optparse
import glob

import django
django.setup()
from xgds_core.models import GroupFlight, NamedURL
from xgds_core.util import build_relative_path

import re
from datetime import timedelta

# Where we expect dive plans to be underneath 'processed'
DIVE_PLAN_EXPECTED_PATH = "dive_plans"


def add_to_last_key(result, key, value):
    """
    Append a string to the last string for the given key.
    Supports dot notation for the summary section time area
    """
    if 'times.' in key:
        times_list = result['times']
        specific_dict = times_list[-1]
        specific_dict['description'] = '%s %s' % (specific_dict['description'], value)
    else:
        result[key] = '%s %s' % (result[key], value)
    return result


def build_time(input_time, last_time, first=False):
    """
    Construct datetime objects from 4 digit hourminute strings
    :param input_time: HHMM string
    :param last_time: the last datetime to use as starting point.
    :return: a datetime using the given hours and minutes
    """
    hours = int(input_time[:2])
    minutes = int(input_time[2:])
    if first or hours > last_time.hour:
        result = last_time.replace(hour=hours, minute=minutes)
    else:
        # add a day
        last_time = last_time + timedelta(days=1)
        result = last_time.replace(hour=hours, minute=minutes)
    return result


def connect_dive_plan(group_flight, dive_summary_file):
    """
    Search for the dive plan for this group flight based on expected path.
    :param group_flight: the group flight
    :param dive_summary_file: the full path to the dive summary
    :return: the relative path to the dive plan if found, None otherwise
    """
    original_dirname = os.path.dirname(dive_summary_file)
    splits = original_dirname.split('/')[0:-2]
    splits.append(DIVE_PLAN_EXPECTED_PATH)
    new_dirname = ''
    for s in splits:
        new_dirname = "%s%s/" % (new_dirname, s)
    pattern = '%s*%s*' % (new_dirname, group_flight.name)
    result = glob.glob(pattern)
    if result:
        relative_path = build_relative_path(result[-1])  # we really only expect one
        named_url = NamedURL(name='Dive Plan', url=relative_path, content_object=group_flight)
        named_url.save()
        return relative_path
    return None


def read_dive_summary(filename, dive_start_time):
    """
    Read the dive summary and store its values an ordered dict
    :param filename: the name of the dive summary file
    :return: the number of dive summary files successfully read (with data)
    """
    result = {}
    times = []
    result['times'] = times

    f = open(filename, "r")
    lines = f.readlines()
    last_key = None
    last_time = dive_start_time

    first = True
    for line in lines:
        if line.startswith('#'):
            continue

        if not line:
            last_key = None
            continue

        first_char = line[0]
        if first_char.isdigit():
            # 1021	1126	In water - on bottom
            match = re.search('(\d{4})\s+(\d{4})\s+(.+)', line)
            if match:
                value = match.groups()[-1]
                start_string = match.groups()[0]
                end_string = match.groups()[1]
                start_time = build_time(start_string, last_time, first)
                if first:
                    first = False
                end_time = build_time(end_string, start_time, first)
                last_time = end_time

                description = match.groups()[2]
                iso_start = start_time.isoformat()
                block = {'start': iso_start,
                         'end': end_time.isoformat(),
                         'description': description}
                times.append(block)
                last_key = 'times.%s' % iso_start
            elif last_key:
                add_to_last_key(result, last_key, line)

        elif first_char.isalpha():
            index = line.index(': ')
            if index > 0:
                key = line[0:index]
                value = line[index+2:].strip()
                if value:
                    result[key] = value
                last_key = key
            elif last_key:
                result[last_key] = '%s %s' % (result[last_key], line)

    if "" in result:
        del result[""]

    return result


def load_dive_summary(filename):
    """
    Read the file and store it in the extras of the group flight
    :param filename: the filename to read
    :return: the number of keys loaded in the resulting dictionary
    """

    split_filename = os.path.basename(filename).split('-')
    group_flight = GroupFlight.objects.get(name=split_filename[0])

    herc_flight = group_flight.flights.get(vehicle__name='Hercules')
    start_time = herc_flight.start_time
    start_time = start_time.replace(microsecond=0, second=0)

    dive_plan = connect_dive_plan(group_flight, filename)
    if not dive_plan:
        print "DIVE PLAN NOT FOUND FOR %s" % group_flight.name

    loaded_dict = read_dive_summary(filename, start_time)
    if not loaded_dict:
        print "NO VALUES LOADED FROM %s" % filename
        return 0

    group_flight.extras.update(loaded_dict)
    group_flight.save()

    return len(loaded_dict)


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')

    opts, args = parser.parse_args()
    stats_file = args[0]
    loaded = load_dive_summary(stats_file)
