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

import argparse
import yaml

from django.utils import timezone
import django
django.setup()

from xgds_subsea_app.importer.redis_dive_creator import DiveCreator
from xgds_core.flightUtils import getActiveFlight, end_group_flight
from xgds_video.recordingUtil import stopFlightRecording
from django.conf import settings


def get_active_dive():
    active_flight = getActiveFlight()
    if active_flight is not None:
        # there's an active flight underway
        active_dive = active_flight.group
        print 'found active dive %s ' % active_dive.name
        return active_dive
    return None


def create_dive(dive_name, dive_creator):
    """
    Creates and starts the dive
    :param dive_name:
    :param dive_creator:
    :return:
    """

    # first check if there is an active dive
    active_dive = get_active_dive()
    if active_dive:
        stop_dive(active_dive.name)
    print "Creating dive %s" % dive_name
    dive_creator.start_dive(dive_name, timezone.now())


def stop_video_recording(active_dive):
    if not active_dive:
        return
    totalFlights = active_dive.flights.count()
    flightCount = 0
    endEpisode = False  # Flag to stopRecording to end video episode
    for flight in active_dive.flights:
        flightCount += 1
        if flightCount == totalFlights:
            endEpisode = True  # End video episode when we stop last flight in list
        stopFlightRecording(flight.name, endEpisode)


def stop_dive(dive_name):
    """
    Stop a dive
    :param dive_name:
    :return:
    """
    print "Stopping dive %s" % dive_name
    if settings.XGDS_VIDEO_ON:
        stop_video_recording(get_active_dive())
    end_group_flight(dive_name, timezone.now())


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stop', action='store_true', help='Stop dive')
    parser.add_argument('-n', '--name', help='Name of the dive, ie H1745')
    args, unknown = parser.parse_known_args()

    with open('/root/xgds_subsea/apps/xgds_subsea_app/importer/redis_dive_creator_config.yaml') as fp:
        config = yaml.load(fp)

    dc = DiveCreator(config)

    if not args.stop:
        create_dive(args.name, dc)
    else:
        stop_dive(args.name)



