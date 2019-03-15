#!/usr/bin/env python

import os
import stat
import datetime
import json

from uuid import uuid4
from tzlocal import get_localzone
from glob import glob
from os.path import basename
import dateutil.parser as dateparse
from validateCinedekVideo import checkVideoIntegrity
from validateCinedekVideo import VideoSegmentJsonEncoder

SEGMENT_SUMMARY_FILE_NAME = "segmentSummary.json"
FFMPEG_FILE_LIST_BASE = "ffmpegFiles_%03d.txt"
FULL_VEHICLE_NAME = {"HERC": "Hercules", "ARGUS": "Argus"}
PRIMARY_ROV = "HERC"
SECONDARY_ROV = "ARGUS"

def makedirsIfNeeded(path):
    """
    Create dirs with good permissions
    """
    if not os.path.exists(path):
        currentUmask = os.umask(0)  # Save current umask and set to 0 so we can control permissions
        os.makedirs(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        os.umask(currentUmask)  # Restore process umask

def writeSegmentSummaryFile(segList, diveDir, vehicleName, dataDir):
    diveName = basename(diveDir)
    videoDirPath = "%s/%s_%s/Video/Recordings" % (dataDir, diveName, vehicleName)
    makedirsIfNeeded(videoDirPath)
    segmentSummaryFilePath = "%s/%s" % (videoDirPath, SEGMENT_SUMMARY_FILE_NAME)
    segmentSummary = {"vehicle": vehicleName, "flight": "%s_%s" % (diveName, FULL_VEHICLE_NAME[vehicleName]),
                      "videoDir": diveDir, "segments": segList, "uuid": str(uuid4()),
                      "dateProcessed": datetime.datetime.now(get_localzone()).strftime("%Y-%m-%d %H:%M:%S %Z")}

    # Write overall segment summary for import to database
    if not os.path.exists(segmentSummaryFilePath):
        fp = open(segmentSummaryFilePath, "w")
        json.dump(segmentSummary, fp, cls=VideoSegmentJsonEncoder)
        fp.close()
    else:
        print "****** WARNING: Segment summary already exists for %s. Will not overwrite. ******" % segmentSummaryFilePath

    for index, seg in enumerate(segList):
        ffmpegFilePath = videoDirPath + "/" + FFMPEG_FILE_LIST_BASE % index
        if not os.path.exists(ffmpegFilePath):
            fp = open(ffmpegFilePath, "w")
            for f in seg.fileList:
                fp.write("file %s/%s/%s\n" % (diveDir, vehicleName, f))
            fp.close()
        else:
            print "****** WARNING: FFMPEG segment list already exists: %s. Will not overwrite. ******" % ffmpegFilePath


def computeEpisodeLengths(diveNamePattern, dataDir, updateSegmentFiles):
    diveDirList = glob("%s/%s" % (dataDir, diveNamePattern))
    diveDirList.sort()
    for d in diveDirList:
        otherRovDir = d.replace(PRIMARY_ROV, SECONDARY_ROV)
        diveName = basename(d)
        print "****************************** Processing %s ******************************\n" % diveName
        hercSegments = json.load(open("%s/Video/Recordings/%s" % (d, SEGMENT_SUMMARY_FILE_NAME), "r"))
        argusSegments = json.load(open("%s/Video/Recordings/%s" % (otherRovDir, SEGMENT_SUMMARY_FILE_NAME), "r"))
        minHerc = hercSegments["segments"][0]["startTime"]
        maxHerc = hercSegments["segments"][0]["endTime"]
        minHercDT = dateparse.parse(minHerc + "Z")
        maxHercDT = dateparse.parse(maxHerc + "Z")

        minArgus = argusSegments["segments"][0]["startTime"]
        maxArgus = argusSegments["segments"][0]["endTime"]
        minArgusDT = dateparse.parse(minArgus + "Z")
        maxArgusDT = dateparse.parse(maxArgus + "Z")
        
        if minHercDT < minArgusDT:
            episodeStart = minHerc
        else:
            episodeStart = minArgus

        if maxHercDT > maxArgusDT:
            episodeEnd = maxHerc
        else:
            episodeEnd = maxArgus

        print "   Herc Start: %s --    Herc End: %s" % (minHercDT, maxHercDT)
        print "  Argus Start: %s --   Argus End: %s" % (minArgusDT, maxArgusDT)
        print "Episode Start: %s -- Episode End: %s" % (episodeStart, episodeEnd)
        hercSegments["episodeStart"] = episodeStart
        hercSegments["episodeEnd"] = episodeEnd
        argusSegments["episodeStart"] = episodeStart
        argusSegments["episodeEnd"] = episodeEnd
        json.dump(hercSegments, open("%s/Video/Recordings/%s" % (d, SEGMENT_SUMMARY_FILE_NAME), "w"))
        json.dump(argusSegments, open("%s/Video/Recordings/%s" % (otherRovDir, SEGMENT_SUMMARY_FILE_NAME), "w"))
        print "\n"

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataDir', required=False, default=None,
                        help="Path to xGDS data directory root. E.g. /home/xgds/xgds_subsea/data")
    parser.add_argument('--diveNamePattern', required=False, default="H[0-9][0-9][0-9][0-9]_HERC",
                        help="Glob regex for dive names. Default: H[0-9][0-9][0-9][0-9]_HERC")
    parser.add_argument('--updateSegmentFiles', required=False, default=False, action="store_true",
                        help="Write JSON summary of episodes to segment summary file")
    args, unknown = parser.parse_known_args()
    baseDir = "foo"
    updateSegmentFiles = args.updateSegmentFiles
    if updateSegmentFiles and not args.dataDir:
        print "You must specify a data directory root with --dataDir option to store segment summary JSON files."
    print "Processing video in:", args.dataDir

    computeEpisodeLengths(args.diveNamePattern, args.dataDir, updateSegmentFiles)
