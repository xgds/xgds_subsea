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

from datetime import datetime

from xgds_planner2.planExporter import TreeWalkPlanExporter
from xgds_planner2 import xpjson
from xgds_planner2.models import getPlanSchema

from geocamUtil.ProjUtil import get_projection, ll_to_utm


class TgtPlanExporter(TreeWalkPlanExporter):
    """
    Exports stations as space separated target strings
    """
    label = 'tgt'
    content_type = 'text/csv'

    def __init__(self):
        self.csvWriter = None

        self.separator = " "

        # set the times
        self.utc_now = datetime.utcnow()
        self.hms = self.utc_now.strftime('%H:%M:%S')
        self.mdy = self.utc_now.strftime('%m/%d/%Y')

        self.utm_zone = ''
        self.projection = None

    def initPlan(self, plan, context):
        self.south = False
        if plan.site.alternateCrs:
            zone_number = plan.site.alternateCrs['properties']['zone']
            zone_letter = plan.site.alternateCrs['properties']['zoneLetter']

            self.utm_zone = '%s%s' % (zone_number, zone_letter)

            if zone_letter:
                if zone_letter < 'N':
                    self.south = True

        self.projection = get_projection(self.utm_zone, self.south)

    def transformStation(self, station, tsequence, context):
        # GPT "name" easting northing 0.00 latitude longitude hh:mm:ss MM/DD/YYYY 0.00 0.00 0 0 0.00 "notes" "SY(POSGEN03,0)" 0.0
        # GPT "Test1" 273387.37 2100940.52 0.00 18.98849991667 -155.15254155556 15:38:26 08/31/2018 0.00 0.00 0 0 0.00 "" "SY(FLTHAZ02,0)" 0.0

        lon, lat = station.geometry['coordinates']
        easting, northing = ll_to_utm(lon, lat, self.projection)
        name = station.name
        if not name:
            name = station.id
        notes = station.notes
        if not notes:
            notes = ""

        result = 'GPT "%s" %.2f %.2f 0.00 %.11f %.11f %s %s 0.00 0.00 0 0 0.00 "%s" "SY(POSGEN03,0)" 0.0\n' % \
                 (name, easting, northing, lat, lon, self.hms, self.mdy, notes)

        return result

    def transformSegment(self, segment, tsequence, context):
        return None

    def transformPlan(self, plan, tsequence, context):
        return tsequence


