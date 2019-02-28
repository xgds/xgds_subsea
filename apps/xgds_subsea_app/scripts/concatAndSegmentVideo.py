#!/usr/bin/env python

import os
import stat
import datetime
import json
import subprocess

from uuid import uuid4
from tzlocal import get_localzone
from glob import glob
from os.path import basename, splitext
from validateCinedekVideo import checkVideoIntegrity
from validateCinedekVideo import VideoSegmentJsonEncoder

SEGMENT_SUMMARY_FILE_NAME = "segmentSummary.json"
FFMPEG_FILE_LIST_PATTERN = "ffmpegFiles_[0-9][0-9][0-9].txt"
FULL_VEHICLE_NAME = {"HERC": "Hercules", "ARGUS": "Argus"}
VIDEO_SUBDIR_PATH = "Video/Recordings"


def getSegNumString(ffmpegFilepath):
    root, ext = splitext(basename(ffmpegFilepath))
    segNumStr = root.split("_")[1]
    return segNumStr


def processVideoFiles(dataDir, diveNamePattern, skipConcat, skipHLS, deleteConcatFile):
    diveDirList = glob("%s/%s" % (dataDir, diveNamePattern))
    diveDirList.sort()
    for d in diveDirList:
        ffmpegFiles = glob("%s/%s/%s" % (d, VIDEO_SUBDIR_PATH, FFMPEG_FILE_LIST_PATTERN))
        ffmpegFiles.sort()
        diveName = basename(d)
        print "****************************** Processing %s ******************************\n" % diveName
        for f in ffmpegFiles:
            fileName = basename(f)
            print "=============== %s ===============" % fileName
            segNum = getSegNumString(fileName)
            concatFilePath = "%s/%s/Segment%s.mp4" % (d, VIDEO_SUBDIR_PATH, segNum)
            segmentDirPath = "%s/%s/Segment%s" % (d, VIDEO_SUBDIR_PATH, segNum)
            if not skipConcat:
                print "Building concatenated file: Segment%s.mp4" % segNum
                res = subprocess.call(["ffmpeg", "-f", "concat", "-safe", "0", "-i", f, "-map",  "0:0", "-map", "0:2",
                                       "-c", "copy", concatFilePath])
                if res != 0:
                    print "*** FFMPEG error - exiting ***"
                    exit(res)
            if not skipHLS:
                if not os.path.isdir(segmentDirPath):
                    os.mkdir(segmentDirPath)
                print "Building HLS segments..."
                res = subprocess.call(["mediafilesegmenter", "-t5", "--start-segments-with-iframe",
                                       "-f", segmentDirPath, concatFilePath])
                if res != 0:
                    print "*** HLS encoding error - exiting ***"
                    exit(res)
            if deleteConcatFile:
                print "Delete concatenated video segments"
                os.remove(concatFilePath)


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataDir', required=True, default=None,
                        help="Path to xGDS data directory root. E.g. /home/xgds/xgds_subsea/data")
    parser.add_argument('--diveNamePattern', required=False, default="H[0-9][0-9][0-9][0-9]_*",
                        help="Glob regex for dive names. Default: H[0-9][0-9][0-9][0-9]")
    parser.add_argument('--skipConcat', required=False, default=False, action="store_true",
                        help="Skip concatenation of Cinedek video files. Only do this if already processed.")
    parser.add_argument('--skipHLS', required=False, default=False, action="store_true",
                        help="Don't run the HLS segmenter.")
    parser.add_argument('--deleteConcatFile', required=False, default=True, action="store_true",
                        help="By default, we delete the concatenated video file after segments built.")
    args, unknown = parser.parse_known_args()
    print "Processing video in:", args.dataDir
    print "Dive search pattern:", args.diveNamePattern
    print "Skip concat:", args.skipConcat
    print "Skip HLS:", args.skipHLS
    print "Delete concatenated video file:", args.deleteConcatFile

    processVideoFiles(args.dataDir, args.diveNamePattern, args.skipConcat, args.skipHLS, args.deleteConcatFile)
