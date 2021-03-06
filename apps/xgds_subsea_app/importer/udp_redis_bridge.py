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
import socket
import redis
import threading
from time import sleep

import django
django.setup()
from django.conf import settings
from xgds_core.util import persist_error


class UdpRedisBridge:
    def __init__(self, config):
        self.verbose = config['verbose']
        self.udp_host = config['host']
        self.udp_port = config['port']

        # bind socket for udp stream coming in
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.udp_host, self.udp_port))

        # Redis connection for messages going out
        self.r = redis.Redis(host=settings.XGDS_CORE_REDIS_HOST, port=settings.XGDS_CORE_REDIS_PORT)
        self.channel_name = config['channel']

        # Start a thread for this UDP to that Redis channel
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        print 'bridging udp port %d -> redis "%s"' % (self.udp_port, self.channel_name)
        connected = True
        while connected:
            try:
                rcv = self.socket.recv(2048).strip()
                if len(rcv) < 1:
                    print 'DISCONNECTED %s' % self.channel_name
                    connected = False
                else:
                    # status message showing the udp port data came in,
                    # the redis channel it is goingn to, and the contents
                    # of the message
                    if self.verbose:
                        print '%d->%s: %s' % (self.udp_port, self.channel_name, rcv)
                    self.r.publish(self.channel_name, rcv)
            except Exception as e:
                persist_error(e)

        self.socket.shutdown()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print "You must pass yaml file path as the first argument"
        exit(1)

    yaml_file = sys.argv[1]
    with open(yaml_file, 'r') as fp:
        config = yaml.load(fp)

    if 'bridges' in config:
        bridges = []
        for name, params in config['bridges'].iteritems():
            bridges.append(UdpRedisBridge(params))
        while True:
            sleep(1)
