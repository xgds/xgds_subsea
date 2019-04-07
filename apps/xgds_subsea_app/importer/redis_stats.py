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
import yaml
import pytz
import json
import redis
import curses
import datetime
import threading
from time import sleep

import django

django.setup()
from django.conf import settings

from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder


class TelemetryCounter:
    def __init__(self, listen_interval=0.005, publish_channel=None, publish_interval=None):
        self.listen_interval = listen_interval
        self.stats = {}
        # Redis connection
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        # Redis subscription & confirmation
        self.ps = self.r.pubsub(ignore_subscribe_messages=True)
        # subscription request:
        self.ps.psubscribe('*')

        # for publishing stats
        self.publish = False
        if publish_channel is not None and publish_interval is not None:
            self.publish = True
            self.publish_channel = publish_channel
            self.publish_interval = datetime.timedelta(seconds=publish_interval)
            self.publish_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def update_stats(self):
        msg = self.ps.get_message()
        while msg is not None:
            channel = msg['channel']
            if channel not in self.stats:
                self.stats[channel] = {}
                self.stats[channel]['count'] = 0
                self.stats[channel]['last'] = None
            self.stats[channel]['count'] += 1
            self.stats[channel]['last'] = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
            msg = self.ps.get_message()

    def publish_stats(self):
        msg = json.dumps(self.stats, cls=DatetimeJsonEncoder)
        self.r.publish(self.publish_channel, msg)
        self.publish_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

    def run(self):
        while True:
            sleep(self.listen_interval)
            self.update_stats()
            if self.publish:
                age = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - self.publish_time
                if age >= self.publish_interval:
                    self.publish_stats()


def drawer(stdscr, telem_counter):
    while True:
        channel_names = sorted(telem_counter.stats.keys())
        if len(channel_names) > 0:
            name_width = len(max(channel_names, key=len))
            count_width = 8
            time_width = len('2000-01-01 12:00:00.000000+00:00')
            fmt = '%%%ds %%%dd %%%ds' % (name_width, count_width, time_width)

            # redraw the table
            stdscr.erase()
            for i, channel in enumerate(channel_names):
                stdscr.addstr(i, 0, fmt % (channel,
                                           telem_counter.stats[channel]['count'],
                                           telem_counter.stats[channel]['last'].isoformat()))
            stdscr.move(len(channel_names), 0)
            stdscr.refresh()
        sleep(0.1)


def main():
    yaml_file = sys.argv[1]
    with open(yaml_file, 'r') as fp:
        config = yaml.load(fp)

    if 'pubsub' in config:
        tc = TelemetryCounter(**config['pubsub'])
    else:
        tc = TelemetryCounter()

    if 'display' in config and config['display']:
        # curses event loop will take over
        curses.wrapper(drawer, tc)
    else:
        # need our own sleep loop to keep the telemetry counter thread alive
        while True:
            sleep(1)


if __name__ == '__main__':
    main()
