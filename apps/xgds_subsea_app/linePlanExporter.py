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

SEPARATOR = ' '


class LinePlanExporter(TreeWalkPlanExporter):
    """
    Exports plan as a line file for Hypack.  This is a csv file
    """
    label = 'line'
    content_type = 'text/csv'

    def transformStation(self, station, tsequence, context):
        return None

    def transformSegment(self, segment, tsequence, context):

        name = segment.name
        if not name:
            name = segment.id
        lon1, lat1 = context.prevStation.geometry['coordinates']
        lon2, lat2 = context.nextStation.geometry['coordinates']

        result = "%s%s%.11f%s%.11f%s%.11f%s%.11f\n" % (name, SEPARATOR, lat1, SEPARATOR, lon1, SEPARATOR,
                                                       lat2, SEPARATOR, lon2)
        return result

    def transformPlan(self, plan, tsequence, context):
        first_row = "Name%sStartLat%sStartLon%sEndLat%sEndLon\n" % (SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR)
        tsequence.insert(0, first_row)
        return tsequence

