#!/usr/bin/env python

from glob import glob
import xml.etree.ElementTree as ET
from timecode import Timecode
from os.path import splitext, basename

CINEDEK_FRAME_RATE= 29.97

def checkForMissingFiles(videoDir):
    movFileList = glob("%s/*.mov" % videoDir)
    xmlMetaFileList = glob("%s/*.xml" % videoDir)
    # We can drop the head of the path and file extension.  Want to compare basenames
    # to be sure we have matched pairs of XML metadata and MOV files.
    movFileList = [splitext(basename(f))[0] for f in movFileList]
    xmlMetaFileList = [splitext(basename(f))[0] for f in xmlMetaFileList]

    movFileSet = set(movFileList)
    xmlMetaFileSet = set(xmlMetaFileList)

    movWithNoXml = movFileSet - xmlMetaFileSet
    xmlWithNoMov = xmlMetaFileSet - movFileSet
    
    if len(movWithNoXml) != 0:
        print "These MOV files are missing XML metadata:"
        for f in movWithNoXml:
            print "   ", f

    if len(xmlWithNoMov) != 0:
        print "These XML metadata files are missing MOV files:"
        for f in xmlWithNoMov:
            print "   ", f

    matchedFileSet = movFileSet and xmlMetaFileSet
    matchedFileList = list(matchedFileSet)
    matchedFileList.sort()

    return matchedFileList

def checkForContinuousVideo(videoDir, matchedFileList):
    previousFileInfo = {}
    for f in matchedFileList:
        xmlMetafilePath = "%s/%s.xml" % (videoDir, f)
        docroot = ET.parse(xmlMetafilePath).getroot()
        endTimecode = Timecode(CINEDEK_FRAME_RATE,
                               docroot.find("endTimecode").text)
        startTimecode = Timecode(CINEDEK_FRAME_RATE,
                               docroot.find("startTimecode").text)
        if previousFileInfo:
            prevEndFrameCount = previousFileInfo["endTimecode"].frames
            currentStartFrameCount = startTimecode.frames
            if (currentStartFrameCount - prevEndFrameCount) != 1:
                if currentStartFrameCount < prevEndFrameCount:
                    print "Overlapping video detected!"
                    print "  Ignoring file:", previousFileInfo["filename"]
                else:
                    print "Gap detected (%d frames)!" % (currentStartFrameCount - prevEndFrameCount)
                    print "  Start new segment for:", f
        previousFileInfo["endTimecode"] = endTimecode
        previousFileInfo["filename"] = f

def checkVideoIntegrity(videoDir):
    matchedFileList = checkForMissingFiles(videoDir)
    checkForContinuousVideo(videoDir, matchedFileList)
    
    
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--videoDir', required=True,
                        help="Path to a directory with Herc/Argus Cinedek files")
    args, unknown = parser.parse_known_args()
    videoDir = args.videoDir
    print "Checking integrity of files in:", videoDir
    checkVideoIntegrity(videoDir)

