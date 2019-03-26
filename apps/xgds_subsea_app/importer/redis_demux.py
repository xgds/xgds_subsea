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
import redis
import threading
from time import sleep
from redis_utils import TelemetryQueue

import django
django.setup()
from django.conf import settings


class RedisDemux:
    def __init__(self, channel_config, sleep_time=0.005):
        self.config = channel_config
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        self.tq = TelemetryQueue(self.config['input_channel'], sleep_time)

        # Spawn listener thread
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        print '%s listener started' % self.config['input_channel']
        # polling loop:
        for msg in self.tq.listen():
            payload = msg['data'].split('\t')[3]
            for payload_identifier, output_channel in self.config['outputs'].iteritems():
                strlen = len(payload_identifier)
                if payload[0:strlen] == payload_identifier:
                    if verbose:
                        print '%s %s -> %s' % (self.config['input_channel'],
                                               payload_identifier, output_channel)
                    self.r.publish(output_channel, msg['data'])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "You must pass yaml file path as the first argument"
        exit(1)

    yaml_file = sys.argv[1]
    with open(yaml_file, 'r') as fp:
        config = yaml.load(fp)

    verbose = False
    if 'verbose' in config:
        verbose = config['verbose']

    if 'bridges' in config:
        bridges = []
        for name, params in config['bridges'].iteritems():
            bridges.append(RedisDemux(params))
        while True:
            sleep(1)
