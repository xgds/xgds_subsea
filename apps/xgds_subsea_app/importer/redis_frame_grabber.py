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
from threading import Timer
import traceback
import argparse
import yaml
import pytz
import threading
from time import sleep
from dateutil.parser import parse as dateparser

import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, OperationalError

from redis_utils import TelemetryQueue
from geocamTrack.utils import LazyGetModelByName

from xgds_video.views import grab_frame_from_time

VEHICLE_MODEL = LazyGetModelByName(settings.XGDS_CORE_VEHICLE_MODEL)

# This script listens to frame grab events, and after a delay creates an image set from the frame grab.


def grab_frame(the_time, channel, vehicle,  author):
    """
    Do the actual frame grab
    :param the_time:
    :param channel:
    :return:
    """
    imageset = None
    try:
        print ('Grabbing frame for %s at %s' % (str(vehicle), the_time.isoformat()))
        imageset = grab_frame_from_time(the_time, vehicle, author, vehicle.name)
    except OperationalError:
        print 'Lost db connection, retrying'
        connection.close()
        connection.connect()
        # reset db connection
        imageset = grab_frame_from_time(the_time, vehicle, author, vehicle.name)
    except Exception:
        traceback.print_exc()
    if imageset:
        print 'created image'
        print imageset
        return imageset
    return 'No image created!!!'


class FrameGrabber(object):
    def __init__(self, config, prefix=""):
        self.verbose = config['verbose']
        self.prefix = prefix

        self.delimiter = '\t'
        self.tq = TelemetryQueue(config['channel_name'])
        self.author = User.objects.get(username='importer')
        self.argus = VEHICLE_MODEL.get().objects.get(name='Argus')
        self.hercules = VEHICLE_MODEL.get().objects.get(name='Hercules')

        # Start listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def parse_data(self, data):
        """
        Gets the time and channel from the data
        :param data: the incoming data
        :return: time and channel
        """
        values = data.split(self.delimiter)

        # get the time
        time_value = values[1]
        the_time = dateparser(time_value)
        the_time.replace(tzinfo=pytz.UTC)

        # get the channel
        chan_value = values[2]
        chan = int(chan_value.split('=')[1])
        return the_time, chan

    def run(self):
        for msg in self.tq.listen():
            data = msg['data']
            the_time, channel = self.parse_data(data)
            vehicle = self.hercules
            if channel == 2:
                vehicle = self.argus

            t = Timer(settings.XGDS_VIDEO_RECORDING_LAG_SECONDS, grab_frame, [the_time, channel, vehicle, self.author])
            t.start()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', type=str, help="The yaml configuration file")
    args, unknown = parser.parse_known_args()

    with open(args.yaml_file, 'r') as fp:
        config = yaml.load(fp)

    print('Starting frame grabber')
    dc = FrameGrabber(config)

    while True:
        sleep(1)
