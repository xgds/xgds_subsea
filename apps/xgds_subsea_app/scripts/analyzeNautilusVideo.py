#!/usr/bin/env python

import os
import stat
import datetime
import json

from uuid import uuid4
from tzlocal import get_localzone
from glob import glob
from os.path import basename
from validateCinedekVideo import checkVideoIntegrity
from validateCinedekVideo import VideoSegmentJsonEncoder

SEGMENT_SUMMARY_FILE_NAME = "segmentSummary.json"
FFMPEG_FILE_LIST_BASE = "ffmpegFiles_%03d.txt"
FULL_VEHICLE_NAME = {"HERC": "Hercules", "ARGUS": "Argus"}

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
    videoDirPath = "%s/%s_%s/Video/Recordings" % (dataDir, diveName, FULL_VEHICLE_NAME[vehicleName])
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


def analyzeNautilusVideo(baseDir, diveNamePattern, dataDir, writeSegmentFiles):
    diveDirList = glob("%s/%s" % (baseDir, diveNamePattern))
    diveDirList.sort()
    for d in diveDirList:
        vehicleList = glob("%s/*" % d)
        vehicleList.sort()
        diveName = basename(d)
        print "****************************** Processing %s ******************************\n" % diveName
        for v in vehicleList:
            vehicleName = basename(v)
            print "=============== %s ===============" % vehicleName
            segList = checkVideoIntegrity(v, writeSegmentFiles)
            if segList:
                print "\nWriting summary file with %d segments to %s_%s video directory" % (len(segList),
                                                                                          diveName, vehicleName)
                writeSegmentSummaryFile(segList, d, vehicleName, dataDir)
            print "\n"

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseDir', required=True,
                        help="Path to a directory with one type of video (e.g. HIGH/LOW) from a cruise")
    parser.add_argument('--dataDir', required=False, default=None,
                        help="Path to xGDS data directory root. E.g. /home/xgds/xgds_subsea/data")
    parser.add_argument('--diveNamePattern', required=False, default="H[0-9][0-9][0-9][0-9]",
                        help="Glob regex for dive names. Default: H[0-9][0-9][0-9][0-9]")
    parser.add_argument('--writeSegmentFiles', required=False, default=False, action="store_true",
                        help="Write JSON summary of segments to flight directory")
    args, unknown = parser.parse_known_args()
    baseDir = args.baseDir
    writeSegmentFiles = args.writeSegmentFiles
    if writeSegmentFiles and not args.dataDir:
        print "You must specify a data directory root with --dataDir option to store segment summary JSON files."
    print "Processing video in:", baseDir

    analyzeNautilusVideo(baseDir, args.diveNamePattern, args.dataDir, writeSegmentFiles)
