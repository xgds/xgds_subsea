#!/usr/bin/env python

from glob import glob
import xml.etree.ElementTree as ET
from timecode import Timecode
from os.path import splitext, basename
import datetime
import json
from tzlocal import get_localzone

CINEDEK_FRAME_RATE= 29.97
VIDEO_FILE_EXTENSION = "mov"  # Could be MP4 too, but Cinedek seems to use .mov

class VideoSegment:
    startTime = None
    endTime = None
    fileList = []

    def __init__(self, startTime, endTime, initialFileList):
        self.startTime = startTime
        self.endTime = endTime
        self.fileList = initialFileList

    def __unicode__(self):
        return "Start: %s\nEnd: %s\n%d files." % (self.startTime, self.endTime, len(self.fileList))

    def __str__(self):
        return unicode(self).encode('utf-8')

    def updateEndtimeFromMetadata(self, docroot):
        self.endTime = buildDatetimeFromCinedekMetadata(docroot, "endTimecode")


class VideoSegmentJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, VideoSegment):
            return {"type":"VideoSegment", "startTime":obj.startTime, "endTime": obj.endTime, "fileList":obj.fileList}
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


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

def buildDatetimeFromCinedekMetadata(docroot, timecodeTag, prevDay=False, dateTag="dateTaken"):
    # type: (ET.Element, str, bool, str) -> datetime.datetime
    # The Cinedek metadata stores only the date at the end of the recorded file.  If the recording passes thru
    # midight, set prevDay to True, if you need the correct date for the starting timecode.

    timecode = Timecode(CINEDEK_FRAME_RATE,
                        docroot.find(timecodeTag).text)
    endDateStr = docroot.find(dateTag).text

    # We do a few contortions to get the timecode and date converted to a format that datetime likes. The fractional
    # seconds have to be expressed as a zero padded integer number of microseconds.
    hour, min, sec, frame = timecode.frames_to_tc(timecode.frames)
    frameInMicrosec = str(int(round(1000000*(frame/CINEDEK_FRAME_RATE),0))).zfill(6)
    fullDatetime = datetime.datetime.strptime("%s %02d:%02d:%02d.%s" % (endDateStr, hour, min, sec, frameInMicrosec),
                                             "%Y%m%d %H:%M:%S.%f")
    if prevDay:
        fullDatetime = fullDatetime - datetime.timedelta(days=1)
    return fullDatetime

def makeNewVideoSegment(videoDir, f, appendFile=False):
    xmlMetafilePath = "%s/%s.xml" % (videoDir, f)
    docroot = ET.parse(xmlMetafilePath).getroot()
    endTimecode = Timecode(CINEDEK_FRAME_RATE,
                           docroot.find("endTimecode").text)
    startTimecode = Timecode(CINEDEK_FRAME_RATE,
                             docroot.find("startTimecode").text)

    endDatetime = buildDatetimeFromCinedekMetadata(docroot, "endTimecode")

    # Now we need to check if the start and end of this video "chunk" crossed a midnight boundary and adjust start date
    # accordingly.  Date in Cinedek metadata is at end time of recorded chunk.
    prevDay = True if (endTimecode.frames < startTimecode.frames) else False
    startDatetime = buildDatetimeFromCinedekMetadata(docroot, "startTimecode", prevDay=prevDay)

    if appendFile:
        videoSeg = VideoSegment(startDatetime, endDatetime, ["%s.%s" % (f, VIDEO_FILE_EXTENSION)])
    else:
        videoSeg = VideoSegment(startDatetime, endDatetime, [])
    return videoSeg

def checkForContinuousVideo(videoDir, matchedFileList, dumpSegments):
    previousFileInfo = {}
    videoSegments = []

    currentVideoSegment = makeNewVideoSegment(videoDir, matchedFileList[0])
    videoSegments.append(currentVideoSegment)

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
                    print "  %s overlaps %s" % (previousFileInfo["filename"], f)
                else:
                    print "Gap detected (%d frames)!" % (currentStartFrameCount - prevEndFrameCount)
                    print "  Start new segment for:", f
                    currentVideoSegment = makeNewVideoSegment(videoDir, f)
                    videoSegments.append(currentVideoSegment)
        currentVideoSegment.fileList.append("%s.%s" % (f, VIDEO_FILE_EXTENSION))
        currentVideoSegment.updateEndtimeFromMetadata(docroot)
        previousFileInfo["endTimecode"] = endTimecode
        previousFileInfo["filename"] = f

    if dumpSegments:
        return videoSegments
    else:
        return None

def checkVideoIntegrity(videoDir, dumpSegments):
    matchedFileList = checkForMissingFiles(videoDir)
    segments = checkForContinuousVideo(videoDir, matchedFileList, dumpSegments)
    return segments


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--videoDir', required=True,
                        help="Path to a directory with Herc/Argus Cinedek files")
    parser.add_argument('--vehicle', required=False, default="Vehicle",
                        help="Vehicle name, e.g. 'Hercules' or 'Argus'")
    parser.add_argument('--flight', required=False, default="Flight",
                        help="Flight(dive) name, e.g. H1708")
    parser.add_argument('--dumpSegments', required=False, default=False, action="store_true",
                        help="Path to a directory with Herc/Argus Cinedek files")
    args, unknown = parser.parse_known_args()
    videoDir = args.videoDir
    dumpSegments = args.dumpSegments
    print "Checking integrity of files in:", videoDir
    segments = checkVideoIntegrity(videoDir, dumpSegments)
    if dumpSegments:
        for s in segments:
            print s
        segmentSummary = {"vehicle": args.vehicle, "flight": args.flight, "videoDir": args.videoDir, "segments":segments,
                          "dateProcessed":datetime.datetime.now(get_localzone()).strftime("%Y-%m-%d %H:%M:%S %Z")}
        print json.dumps(segmentSummary, cls=VideoSegmentJsonEncoder)






