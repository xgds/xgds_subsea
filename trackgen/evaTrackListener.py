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

import logging
import datetime
import json
from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder

from zmq.eventloop import ioloop
ioloop.install()

import gevent
from gevent import socket
from gevent.queue import Queue

from geocamUtil.zmqUtil.publisher import ZmqPublisher
from geocamUtil.zmqUtil.util import zmqLoop
import os
from django.core.cache import caches

from xgds_status_board.util import *



DEFAULT_HOST = '10.10.91.5'  # this is for in the field
DEFAULT_HOST = '127.0.0.1'

DEFAULT_PORT = 30000  # this is for in the field
DEFAULT_PORT = 50000

DATA_DELIVERY_PROTOCOL = "UDP"

cache = caches['default']


def socketListenTcp(opts, q):
    logging.info('constructing socket')
    s = socket.socket()
    logging.info('connecting to server at host %s port %s',
                 opts.host, opts.port)
    s.connect((opts.host, opts.port))
    logging.info('connection established')

    buf = ''
    while True:
        buf += s.recv(4096)
        while '\n' in buf:
            line, buf = buf.split('\n', 1)
            q.put(line)

def socketListenUdp(opts, q):
    logging.info('constructing socket')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", int(opts.port)))
    logging.info('Listening for UDP on port %s', opts.port)
    logging.info('connection established')

    buf = ''
    while True:
        data, addr = s.recvfrom(1024)
        data = data.rstrip()
        q.put(data)

def socketListen(opts, q):
    if opts.proto == "UDP":
        socketListenUdp(opts, q)
    if opts.proto == "TCP":
        socketListenTcp(opts, q)


def zmqPublish(opts, q):
    p = ZmqPublisher(**ZmqPublisher.getOptionValues(opts))
    p.start()
    for line in q:
        msg = '%s:%s:%s:' % (opts.dataTopic, opts.evaNumber, opts.trackName) + line
        logging.debug('publishing: %s', msg)
        updateStatus(opts.evaNumber)
        p.pubStream.send(msg)

def updateStatus(evaNumber):
    '''
    update the status in memcache so the status board knows we are listening
    '''

    myKey = "trackListenerEV%s" % str(evaNumber)
    status = {'name': myKey,
              'displayName': 'Track Listener EV%s' % str(evaNumber),
              'statusColor': OKAY_COLOR,
              "refreshRate": 1,
              'lastUpdated': datetime.datetime.utcnow().isoformat()}

    cache.set(myKey, json.dumps(status, cls=DatetimeJsonEncoder))


def evaTrackListener(opts):
    q = Queue()
    jobs = []
    try:
        jobs.append(gevent.spawn(socketListen, opts, q))
        jobs.append(gevent.spawn(zmqPublish, opts, q))
        jobs.append(gevent.spawn(zmqLoop))
        timer = ioloop.PeriodicCallback(lambda: gevent.sleep(0.1), 0.1)
        timer.start()
        gevent.joinall(jobs)
    finally:
        gevent.killall(jobs)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    ZmqPublisher.addOptions(parser, 'tracLinkListener')
    parser.add_option('-p', '--port',
                      default=DEFAULT_PORT,
                      help='TCP or UDP port where EVA track server listens [%default]')
    parser.add_option('-o', '--host',
                      default=DEFAULT_HOST,
                      help='TCP host where EVA track server listens [%default]')
    parser.add_option('--proto',
                      default=DATA_DELIVERY_PROTOCOL,
                      help='UDP or TCP. Use default of UDP in field. [%default]')
    parser.add_option('-n', '--evaNumber',
                      default=1,
                      help=\
                      'EVA identifier for multi-EVA ops. e.g. 1,2... [%default]')
    parser.add_option('-t', '--trackName',
                      default="",
                      help=\
                'Track name to store GPS points. If blank will use active flight then EVA #')
    parser.add_option('-d', '--dataTopic',
                      default="gpsposition",
                      help=\
                'ZMQ topic to publish data record under.  Compass and GPS are on separate topics')
    opts, _args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if not opts.host:
        opts.host = DEFAULT_HOST
        print 'host is %s' % opts.host
    if not opts.port:
        opts.port = DEFAULT_PORT
        print 'port is %d' % opts.port

    evaTrackListener(opts)


if __name__ == '__main__':
    main()
