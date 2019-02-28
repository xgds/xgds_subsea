#__BEGIN_LICENSE__
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
#__END_LICENSE__

import os
import sys
import tempfile
import re

# avoid crazy error on mac os
os.environ['PYTHON_EGG_CACHE'] = '/tmp'

# turn this on to log all headers to /tmp/wsgi
LOG_HEADERS = False


def getEnvironmentFromSourceMe(d='.'):
    # pick up environment variables from sourceme
    fd, varsFile = tempfile.mkstemp('djangoWsgiSourceMe.txt')
    os.close(fd)

    ret = os.system('bash -c "(source %s/sourceme.sh && printenv > %s)"' % (d, varsFile))
    if ret != 0:
        varsFile = '%s/vars.txt' % d
        print >> sys.stderr, 'djangoWsgi.py: could not auto-generate environment from sourceme.sh, trying to fall back to manually generated file %s' % varsFile
        # fallback: user can manually generate vars.txt file by sourcing sourceme.sh and running 'printenv > vars.txt'

    varsIn = file(varsFile, 'r')
    for line in varsIn:
        line = line[:-1]  # chop final cr
        if '=' not in line or '=()' in line:
            continue
        var, val = line.split('=', 1)
        os.environ[var] = val
    varsIn.close()
    try:
        os.unlink(varsFile)
    except OSError:
        pass

    # set up virtualenv if needed
    if 'VIRTUAL_ENV' in os.environ:
        activateFile = '%s/bin/activate_this.py' % os.environ['VIRTUAL_ENV']
        execfile(activateFile, {'__file__': activateFile})

    # add any new entries from PYTHONPATH to Python's sys.path
    if 'PYTHONPATH' in os.environ:
        envPath = re.sub(':$', '', os.environ['PYTHONPATH'])
        sys.path = envPath.split(':') + sys.path


def sendError(start_response, text):
    start_response(text, [('Content-type', 'text/html')])
    return ["""<html>
  <head><title>%s</title></head>
  <body><h1>%s</h1></body>
</html>
    """ % (text, text)]


def downForMaintenance(environ, start_response):
    import stat
    import time
    d = os.path.dirname(os.path.realpath(__file__))
    downFile = os.path.join(d, 'DOWN_FOR_MAINTENANCE')
    downMtime = os.stat(downFile)[stat.ST_MTIME]
    downTimeString = time.strftime('%Y-%m-%d %H:%M %Z', time.localtime(downMtime))
    return sendError(start_response, '503 Down for maintenance since %s' % downTimeString)

thisDir = os.path.dirname(os.path.realpath(__file__))
getEnvironmentFromSourceMe(thisDir)

# do the apache login
import django
django.setup()
from django.conf import settings
from xgds_core.tokenAuth import check_password

# end apache login

# Logging WSGI middleware.

import threading
import pprint
import time
import os


class LoggingInstance:
    def __init__(self, start_response, oheaders, ocontent):
        self.__start_response = start_response
        self.__oheaders = oheaders
        self.__ocontent = ocontent

    def __call__(self, status, headers, *args):
        printable = (status, headers)+args
        pprint.pprint(printable, stream=self.__oheaders)
        self.__oheaders.close()

        self.__write = self.__start_response(status, headers, *args)
        return self.write

    def __iter__(self):
        return self

    def write(self, data):
        self.__ocontent.write(data)
        self.__ocontent.flush()
        return self.__write(data)

    def next(self):
        data = self.__iterable.next()
        self.__ocontent.write(data)
        self.__ocontent.flush()
        return data

    def close(self):
        if hasattr(self.__iterable, 'close'):
            self.__iterable.close()
        self.__ocontent.close()

    def link(self, iterable):
        self.__iterable = iter(iterable)


class LoggingMiddleware:

    def __init__(self, application, savedir):
        self.__application = application
        self.__savedir = savedir
        self.__lock = threading.Lock()
        self.__pid = os.getpid()
        self.__count = 0

    def __call__(self, environ, start_response):
        self.__lock.acquire()
        self.__count += 1
        count = self.__count
        self.__lock.release()

        key = "%s-%s-%s" % (time.time(), self.__pid, count)

        iheaders = os.path.join(self.__savedir, key + ".iheaders")
        iheaders_fp = file(iheaders, 'w')

        icontent = os.path.join(self.__savedir, key + ".icontent")
        icontent_fp = file(icontent, 'w+b')

        oheaders = os.path.join(self.__savedir, key + ".oheaders")
        oheaders_fp = file(oheaders, 'w')

        ocontent = os.path.join(self.__savedir, key + ".ocontent")
        ocontent_fp = file(ocontent, 'w+b')

        errors = environ['wsgi.errors']
        pprint.pprint(environ, stream=iheaders_fp)
        iheaders_fp.close()

        length = int(environ.get('CONTENT_LENGTH', '0'))
        input = environ['wsgi.input']
        while length != 0:
            data = input.read(min(4096, length))
            if data:
                icontent_fp.write(data)
                length -= len(data)
            else:
                length = 0
        icontent_fp.flush()
        icontent_fp.seek(0, os.SEEK_SET)
        environ['wsgi.input'] = icontent_fp

        iterable = LoggingInstance(start_response, oheaders_fp, ocontent_fp)
        iterable.link(self.__application(environ, iterable))
        return iterable


if os.path.exists(os.path.join(thisDir, 'DOWN_FOR_MAINTENANCE')):
    application = downForMaintenance
else:
    #os.environ['DJANGO_SETTINGS_MODULE'] = 'basaltApp.settings'
    from django.core.wsgi import get_wsgi_application
    if LOG_HEADERS:
        logdir = '/tmp/wsgi'
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        application = LoggingMiddleware(get_wsgi_application(), logdir)
    else:
        application = get_wsgi_application()

