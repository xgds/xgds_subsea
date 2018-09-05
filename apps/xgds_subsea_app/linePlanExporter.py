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

from xgds_planner2.planExporter import TreeWalkPlanExporter
from geocamUtil.ProjUtil import get_projection, ll_to_utm

# LNS 1
# LIN 3
# PTS 257646.53 2094241.01
# PTS 258825.98 2088972.79
# PTS 252378.32 2087321.56
# LNN 1
# EOL

class LinePlanExporter(TreeWalkPlanExporter):
    """
    Exports plan as a line file for Hypack.  This is a csv file
    """
    label = 'lnw'
    content_type = 'text/csv'

    utm_zone = ''
    projection = None
    south = False

    def initPlan(self, plan, context):
        if plan.site.alternateCrs:
            zone_number = plan.site.alternateCrs['properties']['zone']
            zone_letter = plan.site.alternateCrs['properties']['zoneLetter']

            self.utm_zone = '%s%s' % (zone_number, zone_letter)

            if zone_letter:
                if zone_letter < 'N':
                    self.south = True

        self.projection = get_projection(self.utm_zone, self.south)

    def transformStation(self, station, tsequence, context):
        name = station.name
        if not name:
            name = station.id

        lon, lat = station.geometry['coordinates']
        easting, northing = ll_to_utm(lon, lat, self.projection)

        result = "PTS %.2f %.2f\n" % (easting, northing)

        return result

    def transformSegment(self, segment, tsequence, context):
        return None

    def transformPlan(self, plan, tsequence, context):
        header ="LNS 1\nLIN %d\n" % len(tsequence)
        tsequence.insert(0, header)
        tsequence.append("LNN %s\nEOL" % plan.name)
        return tsequence

