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

import redis
import datetime
import threading
from time import sleep

import django
django.setup()
from django.conf import settings


class TelemetryQueue:
    def __init__(self,channel_name, sleep_time=0.005):
        self.channel_name = channel_name
        self.sleep_time = sleep_time
        # Redis connection
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        # Redis subscription & confirmation
        self.ps = self.r.pubsub(ignore_subscribe_messages=True)
        # subscription request:
        if str == type(channel_name):
            channel_name = [channel_name]
        for cn in channel_name:
            self.ps.subscribe(cn)

    # check_for_msg() is a non-blocking call
    def check_for_msg(self):
        msg = self.ps.get_message()
        if msg is not None:
            retval = msg['data']
            return retval
        return None

    # returns a generator that blocks until each next message arrives
    def listener(self):
        return self.ps.listener()

    # TODO: delete this method in favor of the built-in redis listener()
    def unnecessary__iter__(self):
        return self

    # TODO: delete this method in favor of the built-in redis listener()
    def unnecessary_next(self):
        # next() is a blocking call, which includes a sleep loop
        # wrapped around a call to redis pubsub get_message()
        # which is not blocking.  If get_message() returns None,
        # sleep and check again until it returns a message
        while True:
            sleep(self.sleep_time)
            msg = self.ps.get_message() # non blocking call, returns message or None
            if msg is not None:
                return msg['data']


class TelemetrySaver(object):
    def __init__(self,options):
        self.config = options

        # redis subscription, sleep loop, buffering, saving records are general
        self.sleep_time = 0.005
        if 'sleep_time' in options:
            self.sleep_time = options['sleep_time']
        self.channel_name = options['channel_name']
        self.buffer = []
        if 'buffer_time_sec' in options:
            self.config['buffer_time_sec'] = options['buffer_time_sec']
            self.last_write_time = datetime.datetime.utcnow()

        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def write_buffer(self):
        if len(self.buffer)>0:
            try:
                print 'saving %d models from %s' % (len(self.buffer),self.channel_name)
                if type(self.buffer[0]) is not None:
                    type(self.buffer[0]).objects.bulk_create(self.buffer)
                    self.buffer = []
                    self.last_write_time = datetime.datetime.utcnow()
            except Exception as e:
                print e
                for entry in self.buffer:
                    print entry

    def deserialize(self,message):
        # Parse an incoming message and return a django object,
        # a list of django objects, or None.  Subclasses need to
        # define this method, there is no generic version
        return None

    def run(self):
        print '%s listener started' % self.channel_name
        tq = TelemetryQueue(self.channel_name)

        while True:
            sleep(self.sleep_time)

            # Each time through:
            #  * check for a new message; if there is one deserialize and buffer it
            #  * check the buffer length; if it's long enough write buffer to the DB
            #  * check the last write time; if it was long enough write buffer to the DB

            # Check for a message; if there is one deserialize and buffer it
            msg = tq.check_for_msg()
            if msg is not None:
                obj = self.deserialize(msg)
                # The result should be None, a model object, or a list of model objects
                if obj is not None:
                    if type(obj) is list:
                        self.buffer.extend(obj)
                    else:
                        self.buffer.append(obj)

            # Check how long it's been and write if it's been too long
            if 'buffer_time_sec' in self.config:
                dt = (datetime.datetime.utcnow() - self.last_write_time).total_seconds()
                if dt >= self.config['buffer_time_sec']:
                    self.write_buffer()

            # Check the buffer length and write if too long
            if 'buffer_length' in self.config:
                if len(self.buffer) >= self.config['buffer_length']:
                    self.write_buffer()
