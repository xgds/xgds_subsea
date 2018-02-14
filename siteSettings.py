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

# siteSettings.py -- site default settings
#
# This contains the default settings for the site-level django app.  This will
# override any application-default settings and define the default set of
# installed applications. This should be a full settings.py file which needs
# minimal overrides by the settings.py file for the application to actually
# function.
#
# As a bare minimum, please edit INSTALLED_APPS!
#
# This file *should* be checked into git.
import importlib
import os
import sys

from django.conf import global_settings
from django.core.urlresolvers import reverse
from geocamUtil.SettingsUtil import getOrCreateDict, getOrCreateArray, HOSTNAME


# Make this unique, and don't share it with anybody.
SECRET_KEY = '***REMOVED***'

#XGDS_BROWSERIFY = getOrCreateArray('XGDS_BROWSERIFY')


# from apps.basaltApp.instrumentDataImporters import *
# apps should be listed from "most specific" to "most general".  that
# way, templates in more specific apps override ones from more general
# apps.
INSTALLED_APPS = ['django_npm_apps',
                  # 'xgds_app'

                  # TODO uncomment the submodules that you are including
                  # 'xgds_sample',
                  # 'xgds_instrument',
                  # 'xgds_notes2',
                  # 'xgds_planner2',
                  # 'xgds_map_server',
                  # 'xgds_data',
                  # 'xgds_image',
                  # 'xgds_video',
                  # 'xgds_plot',
                  # 'xgds_status_board',
                  # 'xgds_core',

                  'deepzoom',
                  'geocamTrack',
                  'geocamPycroraptor2',
                  'geocamUtil',
                  'pipeline',
                  'taggit',
                  'resumable',
                  'django_markwhat',

                  'dal',
                  'dal_select2',
                  'rest_framework.authtoken',
                  'rest_framework',
                  'corsheaders',
                  'django.contrib.admin',
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  ]

for app in INSTALLED_APPS:
    try:
        appSettings = importlib.import_module(app + ".defaultSettings")
        for key, val in vars(appSettings).iteritems():
            if not key.startswith('_'):
                globals()[key] = val
    except:
        pass

USING_DJANGO_DEV_SERVER = ('runserver' in sys.argv)
USE_STATIC_SERVE = USING_DJANGO_DEV_SERVER

SCRIPT_NAME = os.environ['DJANGO_SCRIPT_NAME']  # set in sourceme.sh
if USING_DJANGO_DEV_SERVER:
    # django dev server deployment won't work with other SCRIPT_NAME settings
    SCRIPT_NAME = '/'


DEBUG = True
# TEMPLATE_DEBUG = DEBUG

    
PROJ_ROOT = os.path.abspath(os.path.dirname(__file__))
if not PROJ_ROOT.endswith('/'):
    PROJ_ROOT += '/'

# Python path is agnostic to what the site-level dir is. It also prefers the
# checked-out version of an app over the standard python install locations.
sys.path.append(PROJ_ROOT)

ADMINS = (
    # ('NASA Intelligent Robotics Group', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Databases
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.mysql', # django.db.backends.mysql',
#         'NAME': 'xgds_app',
#         'USER': 'root',
#         'PASSWORD': 'xgds',
#         'HOST': '127.0.0.1',
#         'PORT': '3306',
#     }
# }

#
# If you want to use Bing Maps for a baselayer instead of open street map,
# get an API key from https://www.bingmapsportal.com, and override the
# declaration below in settings.py
XGDS_MAP_SERVER_MAP_API_KEY = ""

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'US/Hawaii'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

SITE_ID = 1  # This is for Django's site framework - NOT to specify the location of a field site.

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds static.
# Example: "/home/static/static.lawrence.com/"
STATIC_ROOT = os.path.join(PROJ_ROOT, "build", "static")

# URL that handles the static served from STATIC_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://static.lawrence.com", "http://example.com/static/"
STATIC_URL = SCRIPT_NAME + 'static/'
EXTERNAL_URL = STATIC_URL

# Absolute path to the directory that holds data. This is different than static
# in that it's uploaded/processed data that's not needed for the operation of
# the site, but may need to be network-accessible, or be linked to from the
# database. Examples: images, generate kml files, etc.
# Example: "/data"
DATA_ROOT = os.path.join(PROJ_ROOT, 'data', '')

# URL that handles the data served from DATA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://data.lawrence.com", "http://example.com/data/"
DATA_URL = SCRIPT_NAME + 'data/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = DATA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = DATA_URL

#  This is the directory appended to MEDIA_ROOT for storing generated deep zooms.
#  If defined, but not physically created, the directory will be created for you.
#  If not defined, the following default directory name will be used:
DEEPZOOM_ROOT = 'xgds_image/deepzoom_images/'

#  These are the keyword arguments used to initialize the deep zoom creator:
#  'tile_size', 'tile_overlap', 'tile_format', 'image_quality', 'resize_filter'.
#  They strike a good (maybe best?) balance between image fidelity and file size.
#  If not defined the following default values will be used:
DEEPZOOM_PARAMS = {'tile_size': 256,
                    'tile_overlap': 1,
                    'tile_format': "jpg",
                    'image_quality': 1.0,
                    'resize_filter': "antialias"}


# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # os.path.join(PROJ_ROOT, 'apps/xgds_app/templates'),
            # os.path.join(PROJ_ROOT, 'apps/xgds_app/templates/xgds_app'),

            # Templates for utility scripts
            os.path.join(PROJ_ROOT, 'bin/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': ['django.template.context_processors.request',
                                   'django.contrib.auth.context_processors.auth',
                                   'django.template.context_processors.debug',
                                   'django.template.context_processors.i18n',
                                   'django.template.context_processors.media',
                                   'django.template.context_processors.static',
                                   'django.template.context_processors.tz',
                                   'django.contrib.messages.context_processors.messages',
                                   'geocamUtil.context_processors.settings',
                                   'geocamUtil.context_processors.AuthUrlsContextProcessor.AuthUrlsContextProcessor',
                                   'geocamUtil.context_processors.SettingsContextProcessor.SettingsContextProcessor'
                                   ],
                    },
        },
    ]


# Session Serializer: we use Pickle for backward compatibility and to allow more flexible session storage, but
# be sure to keep the SECRET_KEY secret for security (see:
# https://docs.djangoproject.com/en/1.7/topics/http/sessions/#session-serialization)
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


# List of callables that know how to import templates from various sources.
# TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',
#                     'django.template.loaders.app_directories.Loader',
#                     #     'django.template.loaders.eggs.load_template_source',
#                     )

MIDDLEWARE_CLASSES = (
    'geocamUtil.middleware.LogErrorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',

#    'reversion.middleware.RevisionMiddleware',
    #'geocamUtil.middleware.SecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend'
]

ROOT_URLCONF = 'urls'

#TODO probably can delete the below 2 lines
LOGIN_URL = SCRIPT_NAME + 'accounts/login/'
LOGIN_REDIRECT_URL = '/'

GEOCAM_UTIL_INSTALLER_USE_SYMLINKS = True
GEOCAM_UTIL_SECURITY_ENABLED = not USING_DJANGO_DEV_SERVER
GEOCAM_UTIL_SECURITY_SSL_REQUIRED_BY_DEFAULT = False
GEOCAM_UTIL_SECURITY_REQUIRE_ENCRYPTED_PASSWORDS = False

GEOCAM_UTIL_SECURITY_LOGIN_REQUIRED_BY_DEFAULT = 'write'

# This is an optional setting but if you don't have it enabled then the map server and the xgds_data won't work
XGDS_DATA_LOG_ENABLED = True

# email settings
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/xgds_messages'
EMAIL_SUBJECT_PREFIX = '[xGDS] '
SERVER_EMAIL = 'noreply@xgds.org'

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.FileSystemFinder',
    'pipeline.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
    'pipeline.finders.CachedFileFinder',
    'djangobower.finders.BowerFinder',
    'django_npm_apps.finders.NpmAppFinder',
)

COMPRESS_ENABLED = True
COMPRESS_CSSTIDY_BINARY = '/usr/bin/csstidy'

# PIPELINE_COMPILERS = ()

DEBUG_TOOLBAR = False
if DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE_CLASSES_LIST = list(MIDDLEWARE_CLASSES)
    MIDDLEWARE_CLASSES_LIST.insert(2, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES_LIST)
    INTERNAL_IPS = ('127.0.0.1', 
                    '10.0.3.1',
                    '::1')  # TODO add your virtual machine's IP here from your host; 
    #ie do an ifconfig and see if virtualbox or vmware has created something.
    # Alternately you can create a view that returns request.META['REMOTE_ADDR']
    DEBUG_TOOLBAR_PANELS = ['debug_toolbar.panels.versions.VersionsPanel',
                            'debug_toolbar.panels.timer.TimerPanel',
                            'debug_toolbar.panels.settings.SettingsPanel',
                            'debug_toolbar.panels.headers.HeadersPanel',
                            'debug_toolbar.panels.request.RequestPanel',
                            'debug_toolbar.panels.sql.SQLPanel',
                            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
                            'debug_toolbar.panels.templates.TemplatesPanel',
                            'debug_toolbar.panels.cache.CachePanel',
                            'debug_toolbar.panels.signals.SignalsPanel',
                            'debug_toolbar.panels.logging.LoggingPanel',
                            'debug_toolbar.panels.redirects.RedirectsPanel',
                            #'debug_toolbar.panels.profiling.ProfilingPanel',
                            ]
    DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False,
                            'RENDER_PANELS': True,
                            'JQUERY_URL': '',
                           }

VAR_ROOT = PROJ_ROOT + 'var/'

# XGDS_PLANNER_SCHEMAS = {
#    "EV": {
#        "schemaSource": "apps/xgds_app/planner/evPlanSchema.json",
#        "librarySource": "apps/xgds_app/planner/evPlanLibrary.json",
#        "simulatorUrl": "xgds_app/js/planner/evSimulator.js",
#        "simulator": "ev.Simulator",
#    }
#}

# GEOCAM_TRACK_RESOURCE_MODEL = 'xgds_app.MyResource'
# GEOCAM_TRACK_RESOURCE_VERBOSE_NAME = 'Asset'
# GEOCAM_TRACK_TRACK_MODEL = 'xgds_app.MyTrack'
# GEOCAM_TRACK_TRACK_MONIKIER = 'Actual_Traverse'
# GEOCAM_TRACK_POSITION_MODEL = 'xgds_app.CurrentPosition'
# GEOCAM_TRACK_PAST_POSITION_MODEL = 'xgds_app.PastPosition'
# GEOCAM_TRACK_INTERPOLATE_MAX_SECONDS = 120

# GEOCAM_TRACK_OPS_TIME_ZONE: split days at midnight in the specified time zone
# TODO must support multiple time zones ...
GEOCAM_TRACK_OPS_TIME_ZONE = TIME_ZONE

COMPASS_EQUIPPED_VEHICLES = []
# FOR HI IT IS
COMPASS_CORRECTION =  10

# XGDS_SAMPLE_SAMPLE_MODEL = 'xgds_app.MySample'

# XGDS_PLANNER2_FLIGHT_MONIKER = "EVA"
# XGDS_PLANNER2_GROUP_FLIGHT_MONIKER = "EVA"
# XGDS_PLANNER2_PLAN_MONIKER = "Planned Traverse"
# XGDS_PLANNER2_STATION_MONIKER = "Waypoint"
# XGDS_PLANNER2_STATION_MONIKER_PLURAL = "Waypoints"
# XGDS_PLANNER2_COMMAND_MONIKER = "Activity"
# XGDS_PLANNER2_COMMAND_MONIKER_PLURAL = "Activities"
# XGDS_PLANNER2_FLIGHT_MODEL = "xgds_app.MyFlight"
# XGDS_PLANNER2_GROUP_FLIGHT_MODEL = "xgds_app.MyGroupFlight"
# XGDS_PLANNER2_ACTIVE_FLIGHT_MODEL = "xgds_app.MyActiveFlight"

#XGDS_PLANNER2_DEFAULT_SITE = ('HIL', 'Hawaii Lava Flows') #'Hawaii Lava Flows'

# XGDS_PLANNER2_SCHEDULE_INCLUDED = True
# XGDS_PLANNER2_SITE_MONIKER = 'Zone'
# XGDS_PLANNER2_PLAN_EXECUTION_MODEL = "xgds_app.MyPlanExecution"

# XGDS_PLANNER2_HANDLEBARS_DIRS = [os.path.join('xgds_planner2', 'templates', 'handlebars'),
                                 # os.path.join('xgds_app', 'templates', 'xgds_planner2'),
                                 # os.path.join('xgds_app', 'templates', 'xgds_sample'),
                                 # os.path.join('xgds_map_server', 'templates', 'handlebars', 'search')]

# XGDS_PLANNER2_EDITOR_CONTEXT_METHOD = 'basaltApp.views.addToPlannerContext'
# XGDS_PLANNER2_SCHEDULE_EXTRAS_METHOD = 'basaltApp.views.addEVToPlanExecution'

# XGDS_PLANNER2_PLOTS = getOrCreateDict('XGDS_PLANNER2_PLOTS')
# XGDS_PLANNER2_PLOTS['Temp'] = 'hi_temp'


# list of (formatCode, extension, exporterClass)
# XGDS_PLANNER_PLAN_EXPORTERS = (
#    ('xpjson', '.json', 'xgds_planner2.planExporter.XpjsonPlanExporter'),
#    ('bearing_distance', '.bdj', 'xgds_planner2.planExporter.BearingDistanceJsonPlanExporter'),
#    ('kml', '.kml', 'xgds_app.kmlPlanExporter.KmlPlanExporter'),
#    ('pml', '.pml', 'xgds_planner2.pmlPlanExporter.PmlPlanExporter'),
# )

# XGDS_NOTES_OPS_TIME_ZONE = GEOCAM_TRACK_OPS_TIME_ZONE
# XGDS_NOTES_USER_SESSION_MODEL = 'xgds_app.MyUserSession'
# XGDS_NOTES_NOTE_MODEL = 'xgds_app.MyNote'
# XGDS_NOTES_TAGGED_NOTE_MODEL = 'xgds_app.MyTaggedNote'
# XGDS_NOTES_POPULATE_NOTE_DATA = 'xgds_app.views.populateNoteData'
# XGDS_NOTES_BUILD_NOTES_FORM = 'xgds_app.views.buildNotesForm'
# XGDS_NOTES_TABLE_DEFAULT_COLUMNS = ['creation_time','event_time', 'event_timezone', 'flight_name', 'author_name', 'role_name', 'location_name', 'content', 'tag_names',  'link']

# XGDS_SAMPLE_HANDLEBARS_DIR = [os.path.join('xgds_sample', 'templates', 'handlebars')]
# XGDS_SAMPLE_PERM_LINK_PREFIX = "https://myapp.xgds.org"

# XGDS_IMAGE_IMAGE_SET_MODEL = 'xgds_app.MyImageSet'
# XGDS_IMAGE_SINGLE_IMAGE_MODEL = 'xgds_app.MySingleImage'
# XGDS_IMAGE_ARROW_ANNOTATION_MODEL = 'xgds_app.ArrowAnnotation'
# XGDS_IMAGE_ELLIPSE_ANNOTATION_MODEL = 'xgds_app.EllipseAnnotation'
# XGDS_IMAGE_RECTANGLE_ANNOTATION_MODEL = 'xgds_app.RectangleAnnotation'
# XGDS_IMAGE_TEXT_ANNOTATION_MODEL = 'xgds_app.TextAnnotation'
# XGDS_IMAGE_DEFAULT_CREATE_DEEPZOOM = True

# XGDS_INSTRUMENT_IMPORT_MODULE_PATH = 'xgds_app.instrumentDataImporters'

# GEOCAM_TRACK_RECENT_TIME_FUNCTION = 'xgds_app.views.getCurrentTimeWithDelayCorrection'

# Include a dictionary of name to url for imports if you wish to include import functionality
# XGDS_DATA_IMPORTS = getOrCreateDict('XGDS_DATA_IMPORTS')
# XGDS_DATA_IMPORTS["Foo"]= '../../xgds_app/instrumentDataImport/Foo'

# XGDS_DATA_MASKED_FIELDS = getOrCreateDict('XGDS_DATA_MASKED_FIELDS')
# XGDS_DATA_MASKED_FIELDS['basaltApp'] = {'MyImageSet': ['user_position',
#                                                           'creation_time',
#                                                           ],
#                                        }
# XGDS_DATA_EXPAND_RELATED = getOrCreateDict('XGDS_DATA_EXPAND_RELATED')
# XGDS_DATA_EXPAND_RELATED['xgds_app'] = {'MySample': [('region', 'zone', 'Zone')]}


# XGDS_VIDEO_GET_ACTIVE_EPISODE = 'xgds_app.views.getActiveEpisode'
# XGDS_VIDEO_GET_EPISODE_FROM_NAME = 'xgds_app.views.getEpisodeFromName'
# XGDS_VIDEO_GET_TIMEZONE_FROM_NAME = 'xgds_app.views.getTimezoneFromFlightName'
# XGDS_VIDEO_INDEX_FILE_METHOD = 'xgds_app.views.getIndexFileSuffix'
# XGDS_VIDEO_DELAY_AMOUNT_METHOD = 'xgds_app.views.getDelaySeconds'
# XGDS_VIDEO_NOTE_EXTRAS_FUNCTION = 'xgds_app.views.getNoteExtras'
# XGDS_VIDEO_NOTE_FILTER_FUNCTION = 'xgds_app.views.noteFilterFunction'

# RECORDED_VIDEO_DIR_BASE = DATA_ROOT
# RECORDED_VIDEO_URL_BASE = DATA_URL


# XGDS_MAP_SERVER_JS_MAP = getOrCreateDict('XGDS_MAP_SERVER_JS_MAP')
# try:
#     del XGDS_MAP_SERVER_JS_MAP['Track']
# except:
#     pass
# XGDS_MAP_SERVER_JS_MAP['Actual_Traverse'] = {'ol': 'geocamTrack/js/olActual_TraverseMap.js',
#                                                        'model': GEOCAM_TRACK_TRACK_MODEL,
#                                                        'columns': ['name', 'resource_name', 'type', 'color', 'alpha',  'pk', 'app_label', 'model_type', 'times', 'coords', 'lat', 'DT_RowId'],
#                                                        'hiddenColumns': ['type', 'color', 'alpha', 'pk', 'app_label', 'model_type', 'times', 'coords', 'lat', 'DT_RowId'],
#                                                        'columnTitles': ['Name', 'Resource',''],
#                                                        'searchableColumns': ['name', 'resource_name'],
#                                                        'search_form_class': 'xgds_app.forms.SearchTrackForm'
#                                                        }

# XGDS_MAP_SERVER_DEFAULT_ZOOM = 15
# XGDS_MAP_SERVER_SITE_MONIKER = 'Region'


PYRAPTORD_SERVICE = True

# XGDS_CURRENT_SITEFRAME_ID = 2  # Hawaii Lava Flows siteframe
# XGDS_CURRENT_REGION_ID = 6 # sample region?
# XGDS_DEFAULT_SAMPLE_TYPE = 2 #'Geology'
# XGDS_CORE_LIVE_INDEX_URL = '/basaltApp/live'


TEST_RUNNER = 'django.test.runner.DiscoverRunner'



def make_key(key, key_prefix, version):
    return key

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 604800,
        'KEY_FUNCTION' : make_key
    }
}

# FILE_UPLOAD_TEMP_DIR = os.path.join(DATA_ROOT, XGDS_MAP_SERVER_GEOTIFF_SUBDIR, 'temp')
ZEROMQ_PORTS = PROJ_ROOT + 'apps/basaltApp/ports.json'


USE_TZ = True

# turn this on when we are live field broadcasting
GEOCAM_UTIL_LIVE_MODE = False
GEOCAM_UTIL_DATATABLES_EDITOR = False
GEOCAM_TRACK_URL_PORT = 8181

XGDS_CORE_TEMPLATE_DIRS = getOrCreateDict('XGDS_CORE_TEMPLATE_DIRS')
# XGDS_CORE_TEMPLATE_DIRS[XGDS_SAMPLE_SAMPLE_MODEL] = [os.path.join('xgds_sample', 'templates', 'handlebars')]
# XGDS_CORE_TEMPLATE_DIRS[XGDS_IMAGE_IMAGE_SET_MODEL] = [os.path.join('xgds_image', 'templates', 'handlebars')]

# XGDS_CORE_CONDITION_MODEL = "xgds_app.MyCondition"
# XGDS_CORE_CONDITION_HISTORY_MODEL = "xgds_app.MyConditionHistory"

XGDS_CORE_REBROADCAST_MAP = getOrCreateDict('XGDS_CORE_REBROADCAST_MAP')
#XGDS_CORE_REBROADCAST_MAP.update({'xgds_app_pastposition':{'modelName':'xgds_app.PastPosition', 'pkColNum':1, 'pkType': 'int'}})

XGDS_CORE_TEMPLATE_DEBUG = True

# COUCHDB_FILESTORE_NAME = "my-file-store"

JWPLAYER_KEY = '***REMOVED***'

# IMAGE_CAPTURE_DIR = os.path.join(DATA_ROOT, 'xgds_video_stills')

# FAVICON_PATH = 'xgds_app/icons/favicon.ico'

ALLOWED_HOSTS = ['*']


# Setup support for proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
         'rest_framework.permissions.IsAuthenticated',
    ]
}

# GEOCAM_TRACK_PRELOAD_TRACK_IMAGES = ["/static/xgds_app/icons/ev1_pointer.png", 
#                                      "/static/xgds_app/icons/ev2_pointer.png",
#                                      "/static/xgds_app/icons/ev1_circle.png", 
#                                      "/static/xgds_app/icons/ev2_circle.png",
#                                      "/static/xgds_app/icons/ev1_stop.png", 
#                                      "/static/xgds_app/icons/ev2_stop.png"]

# XGDS_SSE_TRACK_CHANNELS = ['EV1','EV2']
# XGDS_SSE_CONDITION_CHANNELS = XGDS_SSE_TRACK_CHANNELS
# XGDS_SSE_NOTE_CHANNELS = ['EV1', 'EV2', 'SA']
# XGDS_NOTES_CURRENT_MAPPED_FUNCTION = 'xgds_app.views.currentMapNotes'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 43200 # 12 hours