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
import inspect
import os
from time import sleep

import django

django.setup()
from django.conf import settings
from django.db import connection, OperationalError

from xgds_core.flightUtils import get_default_vehicle, get_vehicle, getActiveFlight


def patch_yaml_path(options):
    """
    Prepend the path to this script to the yaml paths
    :param options: the options that have a yaml path
    :return: the options with the yaml patched
    """
    if '/' not in options['config_yaml']:
        dir_name = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        options['config_yaml'] = os.path.join(dir_name, options['config_yaml'])
    return options


def ensure_vehicle(options):
    """
    Ensure there is a vehicle in the options, uses the default if there is none
    :param options:
    :return: options
    """
    if 'vehicle' not in options or not options['vehicle']:
        options['vehicle'] = get_default_vehicle().name
    return options


def lookup_active_flight(options):
    """
    Looks up a flight given the options
    :param options: a dictionary, should contain the vehicle or it will use the default vehicle
    :return: the found flight, and the flight name and vehicle name in options
    """
    if 'vehicle' not in options:
        vehicle = get_default_vehicle()
        options['vehicle'] = vehicle.name
    else:
        vehicle = get_vehicle(options['vehicle'])
    flight = getActiveFlight(vehicle)
    if not flight:
        options['flight'] = None
    else:
        options['flight'] = flight.name
    return flight


class TelemetryQueue:
    def __init__(self, channel_name, sleep_time=0.005):
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
    def listen(self):
        return self.ps.listen()


class TelemetrySaver(object):
    def __init__(self, options):
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

    def do_write_buffer(self):
        print 'saving %d models from %s' % (len(self.buffer), self.channel_name)
        model = type(self.buffer[0])
        if model is not None:
            model.objects.bulk_create(self.buffer)
            self.buffer = []
            self.last_write_time = datetime.datetime.utcnow()

    def write_buffer(self):
        if len(self.buffer) > 0:
            try:
                self.do_write_buffer()
            except OperationalError:
                # try again
                print 'Lost db connection, retrying'
                connection.close()
                connection.connect()
                self.do_write_buffer()
            except Exception as e:
                print e
                for entry in self.buffer:
                    print entry
                # If we couldn't write it before we won't be able to next time
                # truncate the buffer or it will grow forever
                self.buffer = []

    def deserialize(self, message):
        # Parse an incoming message and return a django object,
        # a list of django objects, or None.  Subclasses need to
        # define this method, there is no generic version
        return None

    def handle_msg(self, msg):
        obj = self.deserialize(msg)
        # The result should be None, a model object, or a list of model objects
        if obj is not None:
            if type(obj) is list:
                if obj:
                    self.buffer.extend(obj)
                    # see if we should broadcast
                    model = type(obj[0])
                    if hasattr(model, 'broadcast'):
                        for m in obj:
                            m.broadcast()
            else:
                self.buffer.append(obj)
                # see if we should broadcast
                if hasattr(obj, 'broadcast'):
                    obj.broadcast()

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
                self.handle_msg(msg)

            # Check how long it's been and write if it's been too long
            if 'buffer_time_sec' in self.config and self.last_write_time:
                dt = (datetime.datetime.utcnow() - self.last_write_time).total_seconds()
                if dt >= self.config['buffer_time_sec']:
                    self.write_buffer()

            # Check the buffer length and write if too long
            if 'buffer_length' in self.config:
                if len(self.buffer) >= self.config['buffer_length']:
                    self.write_buffer()



