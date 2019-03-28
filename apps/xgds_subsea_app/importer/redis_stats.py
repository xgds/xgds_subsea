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

import sys
import redis
import curses
import datetime
import threading
from time import sleep

import django
django.setup()
from django.conf import settings

from xgds_subsea_app.models import TempProbe, ConductivityTempDepth, O2Sat


class TelemetryCounter:
    def __init__(self,sleep_time=0.005):
        self.sleep_time = sleep_time
        self.counters = {}
        self.timers = {}
        # Redis connection
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        # Redis subscription & confirmation
        self.ps = self.r.pubsub(ignore_subscribe_messages=True)
        # subscription request:
        self.ps.psubscribe('*')

        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            sleep(self.sleep_time)
            msg = self.ps.get_message() # non blocking call, returns message or None
            if msg is not None:
                channel = msg['channel']
                if channel not in self.counters:
                    self.counters[channel] = 0
                    self.timers[channel] = None
                self.counters[channel] += 1
                self.timers[channel] = datetime.datetime.utcnow()

    def channels(self):
        return self.counters.keys()

    def count(self,channel):
        return self.counters[channel]

    def time(self,channel):
        return self.timers[channel]

def drawer(stdscr):

    tc = TelemetryCounter()

    # Make stdscr.getch non-blocking
    stdscr.nodelay(True)
    stdscr.clear()

    done = False
    while True:
        c = stdscr.getch()
        # Clear out anything else the user has typed in
        curses.flushinp()
        # If the user presses p, increase the width of the springy bar
        if c == ord('q'):
            done = True

        tc.counters['temp records'] = TempProbe.objects.count()
        if tc.counters['temp records'] > 0:
            tc.timers['temp records'] = TempProbe.objects.all().order_by('-timestamp')[0].timestamp
        else:
            tc.timers['temp records'] = None

        tc.counters['ctd records'] = ConductivityTempDepth.objects.count()
        if tc.counters['ctd records'] > 0:
            tc.timers['ctd records'] = ConductivityTempDepth.objects.all().order_by('-timestamp')[0].timestamp
        else:
            tc.timers['ctd records'] = None

        tc.counters['o2s records'] = O2Sat.objects.count()
        if tc.counters['o2s records'] > 0:
            tc.timers['o2s records'] = O2Sat.objects.all().order_by('-timestamp')[0].timestamp
        else:
            tc.timers['o2s records'] = None

        # redraw the table
        stdscr.erase()
        channel_names = sorted(tc.channels())

        i = 0
        for i,channel in enumerate(channel_names):
            stdscr.addstr(i, 0, '%s: %d %s' % (channel, tc.count(channel), tc.time(channel)))
        stdscr.move(i+1,0)

        sleep(0.1)

def printer():
    tc = TelemetryCounter()

    while True:
        channel_names = sorted(tc.channels())

        i = 0
        for i,channel in enumerate(channel_names):
            print '%s: %d' % (channel,tc.count(channel))

        sleep(1)

curses.wrapper(drawer)
