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

import csv

from xgds_planner2.planExporter import TreeWalkPlanExporter
from xgds_planner2 import xpjson
from xgds_planner2.statsPlanExporter import getDistanceMeters, norm2


def shortPos(latOrLon):
    return float('%.6f' % latOrLon)


def timeHm(total):
    hoursf = total / 3600.0
    hours = int(hoursf)
    minutesf = (hoursf - hours) * 60
    minutes = round(minutesf)

    return '%d:%02d' % (hours, minutes)


class CsvPlanExporter(TreeWalkPlanExporter):
    """
    Exports plan as CSV string.
    """
    label = 'CSV'
    content_type = 'text/csv'

    def __init__(self):
        self.lengthMeters = 0
        self.totalDuration = 0
        self.csvWriter = None
        self.lengths = []

    def getCsvRecord(self, rec):
        result = []
        for name, displayName, value in rec:
            if displayName.startswith('*') or name == 'plan':
                continue
            result.append((name, displayName, value))
        return result

    def getCsvWriter(self, out):
        if not self.csvWriter:
            self.csvWriter = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
        return self.csvWriter

    def writeRecCsv(self, out, rec, doWriteHeader):
        csvWriter = self.getCsvWriter(out)
        csvRec = self.getCsvRecord(rec)
        if doWriteHeader:
            csvWriter.writerow([f[1] for f in csvRec])
        csvWriter.writerow([f[2] for f in csvRec])

    def transformStation(self, station, tsequence, context):
        distMeters = 0
        if context.prevStation:
            distMeters = getDistanceMeters(context.prevStation.geometry['coordinates'],
                                           context.nextStation.geometry['coordinates'])
        self.lengths.append(distMeters)
        self.lengthMeters += distMeters

        lon, lat = station.geometry['coordinates']
        name = station.name
        if not name:
            name = station.id
        stationRecord = (('number', 'Waypoint number',
                          context.stationIndex),
                         ('name', 'Name',
                          name),
                         ('lat', 'Latitude',
                          shortPos(lat)),
                         ('lon', 'Longitude',
                          shortPos(lon)),
                         ('duration', 'Duration of waypoint (H:M)',
                          timeHm(cpt.durationSeconds)),
                         ('cumulativeDuration', 'Time so far (H:M)',
                          timeHm(cpt.cumulativeDurationSeconds)),
                         ('cumulativeDistance', 'Distance so far (meters)',
                          self.lengthMeters),
                         ('notes', 'Notes',
                          station.notes))
        self.writeRecCsv(out, stationRecord, context.stationIndex == 0)

    def transformSegment(self, segment, tsequence, context):
        pass

    def exportPlanInternal(self, plan, context):
        index = 0
        tsequence = []
        for elt in plan.get("sequence", []):
            ctx = context.copy()
            ctx.stationIndex = index
            if elt.type == 'Station':
                ctx.parent = ctx.station = elt
                tsequence.append(self.exportStation(elt, ctx))

            if elt.type == 'Station':
                index += 1

        return self.transformPlan(plan, tsequence, context)

    def test():
        schema = xpjson.loadDocument(xpjson.EXAMPLE_PLAN_SCHEMA_PATH)
        plan = xpjson.loadDocument(xpjson.EXAMPLE_PLAN_PATH, schema=schema)
        exporter = CsvPlanExporter()
        open('/tmp/foo.csv', 'wb').write(exporter.exportPlan(plan, schema))

# OLD SHIT


def writeSegmentsCsv(out, pstruct):
    out.write('SEGMENTS:\n')
    csvWriter = getCsvWriter(out)
    for i in xrange(len(pstruct.segmentList)):
        writeRecCsv(csvWriter, getSegmentRecord(pstruct, i), i == 0)


def writeTargetsCsv(out, pstruct):
    # backward compatible
    if pstruct.targets is None:
        pstruct.targets = {}

    out.write('TARGETS:\n')
    csvWriter = getCsvWriter(out)
    for i, tgtId in enumerate(pstruct.targets.iterkeys()):
        writeRecCsv(csvWriter, getTargetRecord(pstruct, tgtId), i == 0)


def writePlanCsv(request, out, pstruct):
    writePointsCsv(out, pstruct)
    writeSegmentsCsv(out, pstruct)
    writeTargetsCsv(out, pstruct)
