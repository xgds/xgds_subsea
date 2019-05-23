#! /usr/bin/env python
#  __BEGIN_LICENSE__
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
# __END_LICENSE__

import django

django.setup()

import json
import dateutil.parser as dateparse
from xgds_video.models import VideoEpisode, VideoSegment, VideoSource, VideoSettings
from xgds_core.models import Flight
from uuid import uuid4

VIDEO_INDEX_NAME = "prog_index.m3u8"
VIDEO_SEGMENT_DIR_NAME = "Segment"


def createEpisodeIfNeeded(groupFlightName, segmentMetadata):
    # flightInfo = Flight.objects.get(name=segmentMetadata["flight"])
    startTime = dateparse.parse(segmentMetadata["episodeStart"] + "Z")
    endTime = dateparse.parse(segmentMetadata["episodeEnd"] + "Z")
    myEpisode, created = VideoEpisode.objects.get_or_create(
        shortName=groupFlightName,
        defaults={'startTime': startTime,
                  'endTime': endTime,
                  'uuid': segmentMetadata["uuid"]})
    return myEpisode


def getVideoResFromPath(p):
    # Video resolution is 2nd to last element of path to video files
    return p.split("/")[-2:-1][0]


def createSegmentRecord(index, seg, segMeta, videoEpisode):
    videoSource = VideoSource.objects.get(shortName=segMeta["vehicle"])
    videoSettings = VideoSettings.objects.get(name=getVideoResFromPath(segMeta["videoDir"]))
    # NOTE: Cinedek start/end times are unqualified but are in UTC by OET convention.
    startTime = dateparse.parse(seg["startTime"] + "Z")
    endTime = dateparse.parse(seg["endTime"] + "Z")

    seg = VideoSegment(
        directoryName=VIDEO_SEGMENT_DIR_NAME,
        segNumber=index,
        indexFileName=VIDEO_INDEX_NAME,
        startTime=startTime,
        endTime=endTime,
        settings=videoSettings,
        source=videoSource,
        episode=videoEpisode,
        uuid=uuid4())
    seg.save()

    return seg


def main():
    import optparse

    parser = optparse.OptionParser("usage: %prog <metadata JSON file path>")
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.error('path to exactly one metadata JSON file is required')

    print 'processing %s' % args[0]
    segmentMetadata = json.load(open(args[0], "r"))
    groupFlightName = segmentMetadata["flight"].split("_")[0]
    print "  Flight: %s -- Group Flight: %s" % (segmentMetadata['flight'], groupFlightName)
    videoEpisode = createEpisodeIfNeeded(groupFlightName, segmentMetadata)
    for index, seg in enumerate(segmentMetadata["segments"]):
        createSegmentRecord(index, seg, segmentMetadata, videoEpisode)


if __name__ == '__main__':
    main()
