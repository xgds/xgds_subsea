#!/usr/bin/env python
# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
#
#The xGDS platform is licensed under the Apache License, Version 2.0 
#(the "License"); you may not use this file except in compliance with the License. 
#You may obtain a copy of the License at 
#http://www.apache.org/licenses/LICENSE-2.0.
#
#Unless required by applicable law or agreed to in writing, software distributed 
#under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
#CONDITIONS OF ANY KIND, either express or implied. See the License for the 
#specific language governing permissions and limitations under the License.
# __END_LICENSE__

"""
A server that simulates the TracLink server. The server listens
on a TCP port, and clients can connect to receive position data.

By default, the server just replays data from a log of real TracLink
output from a test at KSC. But you can overwrite fields in the records
for your testing convenience using the options.
"""
import socket
import time
import datetime
import pytz
import logging
import os
import math
import calendar
import json
from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder

import django
django.setup()

from django.core.cache import caches
cache = caches['default']

REDIS = False
if REDIS:
    import redis
    import json
    from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
    REDIS_CHANNEL = 'EV2'


# pylint: disable=E1101

EARTH_RADIUS_METERS = 6371010

# When the --fakePos option is specified, the target and the chase
# boat drive in a circle around FAKE_POS_CENTER.

if 0:
    # Pavilion Lake
    FAKE_POS_CENTER_LATITUDE = 51.008101
    FAKE_POS_CENTER_LONGITUDE = -121.776976
    FAKE_POS_RADIUS_METERS = 10000
    FAKE_POS_VELOCITY_METERS_PER_SECOND = 500

if 0:
    # Lake Denton, Central Florida
    FAKE_POS_CENTER_LATITUDE = 27.5562625
    FAKE_POS_CENTER_LONGITUDE = -81.4893358
    FAKE_POS_RADIUS_METERS = 150
    FAKE_POS_VELOCITY_METERS_PER_SECOND = 10

if 0:
    # Nanaimo
    FAKE_POS_CENTER_LATITUDE = 49.207917
    FAKE_POS_CENTER_LONGITUDE = -123.962326
    FAKE_POS_RADIUS_METERS = 100
    FAKE_POS_VELOCITY_METERS_PER_SECOND = 10

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def getLonLat(centerLon, centerLat, dx, dy):
    degrees_per_meter_lat = 1.0 / EARTH_RADIUS_METERS * (180. / math.pi)
    degrees_per_meter_lon = degrees_per_meter_lat / math.cos(centerLat * math.pi / 180.)
    return (centerLon + degrees_per_meter_lon * dx,
            centerLat + degrees_per_meter_lat * dy)


def getFakePosition(dt):
    timeSeconds = calendar.timegm(dt.timetuple())
    angularVelocity = float(FAKE_POS_VELOCITY_METERS_PER_SECOND) / FAKE_POS_RADIUS_METERS
    phase = (timeSeconds * angularVelocity) % (2 * math.pi)
    dx = FAKE_POS_RADIUS_METERS * math.cos(phase)
    dy = FAKE_POS_RADIUS_METERS * math.sin(phase)
    return getLonLat(FAKE_POS_CENTER_LONGITUDE,
                     FAKE_POS_CENTER_LATITUDE,
                     dx, dy)


def computeChecksumString(dataStr):
    cksum = 0
    for c in dataStr:
        cksum = cksum ^ ord(c)
    return "%02X" % cksum


def formatDM(val,nsew):
    hemi = nsew[0] if val > 0 else nsew[1]
    val = abs(val)
    degrees = int(val)
    val = val - degrees
    minutes = val * 60
    return '%d%010.7f,%1s' % (degrees, minutes, hemi)


def evaBackpackGenerator(opts):
    f = open(os.path.join(THIS_DIR, opts.trackFile), "r")
    sampleTrackingData = f.read()

    host = '127.0.0.1'
    port = opts.port
    backlog = 5
    print 'listening on %s:%s' % (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # http://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((host, port))
    s.listen(backlog)

    if REDIS:
        rs = redis.Redis(host='localhost', port=6379)
#         redis_pubsub = rs.pubsub()
        
    while True:
        client, _address = s.accept()
        logging.info('connection established')
        try:
            while True:
                for line in sampleTrackingData.split("\n"):
                    if len(line) != 0:
                        splits = line.split(',')
                        lat = float(splits[0])
                        lon = float(splits[1])
                        hasHeading = False
                        heading = ""
                        if len(splits) > 2:
                            hasHeading = True
                            heading = float(splits[2])
                        now = datetime.datetime.now(pytz.utc)
                        if opts.age:
                            now -= datetime.timedelta(seconds=opts.age)
                            #  for testing live view
                        dateStr = now.strftime("%d%m%y")
                        timeStr = now.strftime("%H%M%S")
                        if opts.fakePositions:
                            # overwrite position
                            lon, lat = getFakePosition(now)
                        lon = formatDM(lon, "EW")
                        lat = formatDM(lat, "NS")
                        
                        # shove compass in memcache FOR ev1
                        if hasHeading:
                            compassRecord = {"compass": heading}
                            cacheKey = 'compass.%s' % opts.resource 
                            cacheRecordDict = {"timestamp": now, "compassRecord": compassRecord}
                            cache.set(cacheKey, json.dumps(cacheRecordDict, cls=DatetimeJsonEncoder))
                        
                        #gpsposition:1:20171105A_EV1:$GPRMC,211808.50,A,1924.7077453,N,15514.6245117,W,0.145,353.2,051117,0.0,E,A*29
                        newLinePreChecksum = ",".join(("GPRMC",
                                                       timeStr+".00", "A",
                                                       lat, lon, "", str(heading),
                                                       dateStr, "0.0,E,A"))
                        checkSum = computeChecksumString(newLinePreChecksum)
                        newLine = "%s%s*%s" % ("$", newLinePreChecksum,
                                               checkSum)
                        logging.info(newLine)
                        client.send(newLine + "\n")
                        
                        if REDIS:
                            if heading == "":
                                heading = None
                            data_dict = {'altitude': 0,
                                         'heading': heading,
                                         'id': 0,
                                         'latitude': lat,
                                         'longitude': lon,
                                         'precisionMeters': None,
                                         'serverTimestamp': None,
                                         'timestamp': now,
                                         'track_id': None,
                                         'type': 'position'}
                            payload_string = json.dumps(data_dict, cls=DatetimeJsonEncoder)
                            message_string = json.dumps({'type':'position', 'data': payload_string})
                            rs.publish(REDIS_CHANNEL, message_string)
                        time.sleep(opts.interval)
        except socket.error:
            logging.warning('socket error. broken pipe? will try to accept another connection')


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog\n' + __doc__)
    parser.add_option('-a', '--age',
                      type='float', default=0.0,
                      help='Age of produced timestamps in seconds [%default]')
    parser.add_option('-i', '--interval',
                      type='float', default=5.0,
                      help='Time between messages in seconds [%default]')
    parser.add_option('-p', '--port',
                      type='int', default=50000,
                      help='Port number to listen for connections [%default]')
    parser.add_option('-f', '--fakePositions',
                      action='store_true', default=False,
                      help='Output fake positions instead of logged positions')
    parser.add_option('-t', '--trackFile',
                      type='str', default='SampleTrack.txt',
                      help='Read lat/lon from this file to generate track')
    parser.add_option('-r', '--resource', default=1, help='id of the resource, 1 for ev1, 2 for ev2')
    opts, args = parser.parse_args()
    if args:
        parser.error('expected no args')
    logging.basicConfig(level=logging.DEBUG)

    evaBackpackGenerator(opts)


if __name__ == '__main__':
    main()
