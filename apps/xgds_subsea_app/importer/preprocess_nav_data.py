#!/usr/bin/env python
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

import os
from glob import glob
from datetime import datetime, timedelta
from xgds_core.importer.csvImporter import CsvImporter, CsvSetImporter
import django
django.setup()

from django.conf import settings

IMPORT_ROOT = os.path.join(settings.DATA_ROOT, 'incoming', settings.CRUISE_ID)
ADDENDUM_XGDS = os.path.join(IMPORT_ROOT, 'addendum', 'xgds')


def interval_sampler(start_time, end_time, interval=timedelta(seconds=1)):
    sample_time = start_time
    while sample_time <= end_time:
        yield sample_time
        sample_time += interval


def current_and_next(iterable):
    iterator = iter(iterable)
    current = next(iterator)
    for next_item in iterator:
        yield current, next_item
        current = next_item


def total_seconds(t1, t2):
    return (t2-t1).total_seconds()


def get_dive_info():
    # Get names, start/end times for all of the dives from dives-stats.tsv
    dive_reader = CsvImporter(os.path.join(settings.PROJ_ROOT, 'apps/xgds_subsea_app/importer/DiveStats.yaml'),
                              os.path.join(IMPORT_ROOT, 'processed/dive_reports/dives-stats.tsv'),
                              replace=True, skip_bad=True)
    dives = dive_reader.load_to_list()
    # unfortunately that includes a header row, so to eliminate that:
    dives = [d for d in dives if '#' not in d['cruise_name']]
    return dives


def filter_telemetry_files(vehicles):
    for vehicle in vehicles:
        # Pre-process telemetry files to get only the rows that contain Herc heading
        raw_files = sorted(glob(os.path.join(IMPORT_ROOT, 'raw/datalog/*_*.HER')))
        for infile in raw_files:
            outfile = os.path.basename(infile).replace('.HER', '.HER-%s' % vehicle['telem_id'])
            outfile = os.path.join(ADDENDUM_XGDS, outfile)
            assert(not outfile == infile)
            if os.path.exists(outfile):
                print '%s already exists' % outfile
                continue
            else:
                cmd = 'grep %s %s > %s' % (vehicle['telem_id'], infile, outfile)
                print cmd
                os.system(cmd)


def interpolate(s1, s2, dt):
    ret = {}
    t1 = s1['timestamp']
    t2 = s2['timestamp']
    for k in s1.keys():
        try:
            a = (dt-t1).total_seconds()/(t2-t1).total_seconds()
        except Exception as e:
            print t1
            print t2
            print dt
            raise e
        if type(s1[k]) is float:
            if k == 'heading':
                # need to handle 359->0 angle wrap-around
                diff = s2[k]-s1[k]
                if diff > 180:
                    diff -= 360
                if diff < -180:
                    diff += 360
                ret[k] = (s1[k] + a*diff) % 360
            else:
                ret[k] = s1[k] + a*(s2[k]-s1[k])
        elif type(s1[k]) is datetime:
            ret[k] = s1[k] + timedelta(seconds=a*(s2[k]-s1[k]).total_seconds())
        else:
            if abs(t1-dt) < abs(t2-dt):
                ret[k] = s1[k]
            else:
                ret[k] = s2[k]
    return ret


def resample_telemetry(telem, start_time, end_time):
    # Temporal samples start on the first full second after the dive start and
    # end on the last full second before the dive ends
    start_second = start_time.replace(microsecond=0) + timedelta(seconds=1)

    next_telem = next(telem)
    print '\tfirst telemetry time:', next_telem['timestamp']
    print '\tstart time:', start_time
    print '\tsampling start:', start_second

    if next_telem['timestamp'] > start_second:
        raise ValueError('Raw telemetry does not cover dive bounds')

    samples = []
    prev_telem = None
    for sample_time in interval_sampler(start_second, end_time):
        # get telemetry values straddling the sample time:
        while next_telem['timestamp'] < sample_time:
            prev_telem = next_telem
            next_telem = next(telem)

        # sanity check
        assert(prev_telem['timestamp'] <= sample_time)
        assert(sample_time <= next_telem['timestamp'])
        assert(prev_telem['timestamp'] < next_telem['timestamp'])

        # interpolate values at this sample_time
        new_sample = interpolate(prev_telem, next_telem, sample_time)
        samples.append(new_sample)

    print '\tdive end:', end_time
    return samples


def resample_attitude_data(dives, vehicles):
    # Get the relevant lines from *.HER files, by grepping for the telemetry
    # identifier (JDS or APAS) and putting the result in a new file to parse later

    for vehicle in vehicles:
        # Parse filtered telemetry files to resample at 1Hz interval
        raw_files = sorted(glob(os.path.join(ADDENDUM_XGDS, '*_*.HER-%s' % vehicle['telem_id'])))
        yaml_file = os.path.join(settings.PROJ_ROOT, 'apps/xgds_subsea_app/importer/HER-%s.yaml' % vehicle['telem_id'])
        telem = CsvSetImporter(yaml_file, raw_files, replace=True)

        for dive in dives:
            print dive['dive_name'], dive['inwatertime'], dive['ondecktime'], dive['totaltime'], 'hours'
            outfile = os.path.join(ADDENDUM_XGDS,
                                   '%s.RPHDA.%s.tsv' % (dive['dive_name'], vehicle['vehicle_id']))
            if os.path.exists(outfile):
                print '%s already exists' % outfile
                continue
            samples = resample_telemetry(telem, start_time=dive['inwatertime'], end_time=dive['ondecktime'])
            write_rphda_file(samples, outfile)


def merge_nav_data(dives, vehicles):
    position_yaml = os.path.join(settings.PROJ_ROOT, 'apps/xgds_subsea_app/importer/NAV.yaml')
    orientation_yaml = os.path.join(settings.PROJ_ROOT, 'apps/xgds_subsea_app/importer/RPHDA.yaml')

    for vehicle in vehicles:
        print 'Vehicle: %s' % vehicle['name']
        for dive in dives:
            outfile = os.path.join(ADDENDUM_XGDS,
                                   '%s.NAV6D.%s.tsv' % (dive['dive_name'], vehicle['vehicle_id']))
            if os.path.exists(outfile):
                print '%s already exists' % outfile
                continue

            # Position file from OET that is already resampled
            position_file = 'processed/dive_reports/%s/merged/%s.NAV3D.%s.sampled.tsv' % \
                            (dive['dive_name'], dive['dive_name'], vehicle['vehicle_id'])
            position_file = os.path.join(IMPORT_ROOT, position_file)
            position_importer = CsvImporter(position_yaml, position_file, replace=True)
            positions = position_importer.load_to_list()

            # Orientation file that we just resampled
            orientation_file = '%s.RPHDA.%s.tsv' % (dive['dive_name'], vehicle['vehicle_id'])
            orientation_file = os.path.join(ADDENDUM_XGDS, orientation_file)
            orientation_importer = CsvImporter(orientation_yaml, orientation_file, replace=True)
            orientations = orientation_importer.load_to_list()

            # Time bounds of the dive, OET positions, and our resampled orientation
            print '  Dive: %s,   %s to %s, %f sec' % (dive['dive_name'], dive['inwatertime'], dive['ondecktime'],
                                                      total_seconds(dive['inwatertime'], dive['ondecktime']))
            print '    %d positions,    %s to %s, %f sec' % (len(positions),
                                                             positions[0]['timestamp'].isoformat(),
                                                             positions[-1]['timestamp'].isoformat(),
                                                             total_seconds(positions[0]['timestamp'],
                                                                           positions[-1]['timestamp']))
            print '    %d orientations, %s to %s, %f sec' % (len(orientations),
                                                             orientations[0]['timestamp'].isoformat(),
                                                             orientations[-1]['timestamp'].isoformat(),
                                                             total_seconds(orientations[0]['timestamp'],
                                                                           orientations[-1]['timestamp']))

            # Iterate through OET positions and pair up our resampled orientation
            orientation_iter = iter(orientations)
            orientation = next(orientation_iter)
            samples = []
            for position in positions:
                while orientation['timestamp'] < position['timestamp']:
                    orientation = next(orientation_iter)
                sample = position
                if not position['timestamp'] == orientation['timestamp']:
                    sample['roll'] = 'None'
                    sample['pitch'] = 'None'
                    sample['heading'] = 'None'
                    sample['altitude'] = 'None'
                else:
                    sample.update(orientation)
                samples.append(sample)

            # Write out the result
            write_nav6d_file(samples, outfile)


# Format float or return empty string for None values
def mystr(number):
    if type(number) is float:
        return '%.6f' % number
    else:
        return number


def write_rphda_file(samples, outfile):
    fp = open(outfile, 'w')
    for s in samples:
        fp.write('\t'.join([s['timestamp'].isoformat(),
                            mystr(s['roll']),
                            mystr(s['pitch']),
                            mystr(s['heading']),
                            mystr(s['depth']),
                            mystr(s['altitude'])]))
        fp.write('\n')
    fp.close()


def write_nav6d_file(samples, outfile):
    fp = open(outfile, 'w')
    for s in samples:
        fp.write('\t'.join([s['timestamp'].isoformat(),
                            mystr(s['latitude']),
                            mystr(s['longitude']),
                            mystr(s['roll']),
                            mystr(s['pitch']),
                            mystr(s['heading']),
                            mystr(s['depth']),
                            mystr(s['altitude'])]))
        fp.write('\n')
    fp.close()


def main():

    # ensure the directory exists
    if not os.path.exists(ADDENDUM_XGDS):
        os.makedirs(ADDENDUM_XGDS)

    # get dive names, start and end times, etc.
    dives = get_dive_info()

    # The telem_id string identifies relevant lines in a mixed CSV file, and vehicle_id is used in OET file names
    vehicles = [{'name': 'Hercules', 'telem_id': 'JDS', 'vehicle_id': 'M1'},
                {'name': 'Argus', 'telem_id': 'APAS', 'vehicle_id': 'M2'}]

    # Filter (grep) raw telemetry files to include only the lines that we will parse in a CsvImporter
    filter_telemetry_files(vehicles)

    # resample raw vehicle attitude telemetry to 1Hz rate and clip to dive start/end
    resample_attitude_data(dives, vehicles)

    # merge resampled attitude with existing resampled location
    merge_nav_data(dives, vehicles)


if __name__ == '__main__':
    main()
