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

import yaml
import redis
import threading
from time import sleep

import django

django.setup()
from django.conf import settings


class RedisDemux:
    def __init__(self, channel_config, sleep_time=0.005):
        self.config = channel_config
        self.sleep_time = sleep_time
        # Redis connection
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        # Redis subscription & confirmation
        self.ps = self.r.pubsub(ignore_subscribe_messages=True)
        # subscription request:
        self.ps.subscribe(self.config['input_channel'])

        # Spawn listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        print '%s listener started' % self.config['input_channel']
        # polling loop:
        while True:
            msg = None
            while msg is None:
                sleep(self.sleep_time)
                msg = self.ps.get_message()  # non blocking call, returns message or None
            if float == type(msg):
                fp = open('msg_float_error.txt')
                fp.write(msg)
                fp.write('\n')
                fp.close()
            payload = msg['data'].split('\t')[3]
            for payload_identifier, output_channel in self.config['outputs'].iteritems():
                strlen = len(payload_identifier)
                if payload[0:strlen] == payload_identifier:
                    if verbose:
                        print '%s %s -> %s' % (self.config['input_channel'],
                                               payload_identifier, output_channel)
                    self.r.publish(output_channel, msg['data'])


if __name__ == '__main__':
    with open('redis_demux_config.yaml', 'r') as fp:
        config = yaml.load(fp)

    verbose = False
    if 'verbose' in config:
        verbose = config['verbose']

    if 'bridges' in config:
        bridges = []
        for name, params in config['bridges'].iteritems():
            bridges.append(RedisDemux(params, sleep_time=0.005))
        while True:
            sleep(1)
