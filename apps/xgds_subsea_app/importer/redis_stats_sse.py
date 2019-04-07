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
import threading
from time import sleep
from redis_utils import TelemetryQueue

import time
import pytz
import datetime
from redis import StrictRedis
import json

import django
django.setup()

from django.conf import settings
from xgds_core.redisUtil import publishRedisSSE


class TelemetryPrinter:
    def __init__(self,channel_name):
        self.channel_name = channel_name
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        print '%s listener started' % self.channel_name
        tq = TelemetryQueue(self.channel_name)
        for msg in tq.listen():
            print '%s: %s' % (self.channel_name, msg)
            publishRedisSSE(
                self.channel_name, 
                self.channel_name, 
                json.dumps({
                    "timestamp": int(time.time()),
                    "message": str(msg),
                },
            ))

if __name__=='__main__':
    TelemetryPrinter("redis_stats")
    while True: sleep(1)
