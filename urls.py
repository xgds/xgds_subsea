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

from django.conf.urls import url, include
from django.conf import settings
from django.contrib.auth.views import login
from django.contrib import auth
from django.views.generic import RedirectView, TemplateView

from django.contrib import admin
admin.autodiscover()

from basaltApp.views import wrist, editInstrumentData

urlpatterns = [url(r'^admin/', include(admin.site.urls)),
               url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
               url(r'^$', RedirectView.as_view(url=settings.SCRIPT_NAME + 'basaltApp/', permanent=False),{}),
               url(r'^accounts/', include('basaltApp.registerUrls')),
               url(r'^basaltApp/', include('basaltApp.urls')),
               url(r'^favicon\.ico$', RedirectView.as_view(url='/static/' + settings.FAVICON_PATH, permanent=True), {'readOnly': True}),
               url(r'^xgds_sample/', include('xgds_sample.urls')),
               url(r'^pycroraptor/', include('geocamPycroraptor2.urls')),
               url(r'^track/', include('geocamTrack.urls')),
               url(r'^xgds_map_server/', include('xgds_map_server.urls')),
               url(r'^xgds_data/', include('xgds_data.urls')),
               url(r'^xgds_image/', include('xgds_image.urls')),
               url(r'^notes/', include('xgds_notes2.urls')),
               url(r'^xgds_planner2/', include('xgds_planner2.urls')),
               url(r'^xgds_plot/', include('xgds_plot.urls')),
               url(r'^xgds_video/', include('xgds_video.urls')),
               url(r'^xgds_instrument/edit/(?P<instrument_name>\w*)/(?P<pk>[\d]+)$', editInstrumentData, {}, 'basalt_instrument_data_edit'),
               url(r'^xgds_instrument/', include('xgds_instrument.urls')),
               url(r'^xgds_core/', include('xgds_core.urls')),
               url(r'^xgds_status_board/', include('xgds_status_board.urls')),
               url(r'^w$', wrist, {'fileFormat':'.kml'}, 'w'),
               ]

if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls)),
                    ]
