
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

from django.conf.urls import include, url

from xgds_core.register import renderTemplate
import restUrls

import xgds_subsea_app.views as views

urlpatterns = [url(r'^$', renderTemplate, {'template_name':'xgds_app/index.html'}, 'index'),
               url(r'^sciChat$', renderTemplate, {'template_name': 'science_chat.html'}, 'science_chat'),
               url(r'^live', views.get_live_page, {}, 'live'),

               # Including these in this order ensures that reverse will return the non-rest urls for use in our server
               url(r'^rest/', include(restUrls)),
               url('', include(restUrls)),
           ]
