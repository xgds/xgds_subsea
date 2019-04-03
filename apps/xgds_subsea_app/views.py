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

from xgds_core.flightUtils import getActiveFlight
from xgds_map_server.views import getGroupFlightPlaybackPage
from django.shortcuts import redirect


def get_live_page(request):
    active_flight = getActiveFlight()
    if active_flight:
        group_flight_name = active_flight.group.name
        return getGroupFlightPlaybackPage(request, group_flight_name,
                                          templatePath='xgds_subsea_app/live_dive.html',
                                          video=False)
    return redirect('index')