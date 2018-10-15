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

from openpyxl import load_workbook
import optparse
import django
django.setup()
from django.core.exceptions import ObjectDoesNotExist

from xgds_sample.models import Sample

"""
The sample sheet pdfs are transcribed into a sample summary xlsx file for the cruise.
This should be called AFTER the event log importer is run, as that will create the sample records.
"""


def clean_value(value):
    """
    Clean the value; if N/A or empty
    :param value: original value
    :return: cleaned value
    """
    if value:
        value = value.strip()

        if value.lower() == 'n/a':
            value = None
        elif value == '':
            value = None
    return value


def import_sample_summary(filename):
    workbook = load_workbook(filename, read_only=True)
    worksheet = workbook.worksheets[0]
    count = 0
    for row in worksheet.rows:
        sample_id = clean_value(row[0].value)
        if sample_id:
            try:
                found_sample = Sample.objects.get(name=sample_id)
                count = count + 1

                extras = found_sample.extras
                extras['wetlab_description'] = clean_value(row[16].value)
                extras['wetlab_description_subsample'] = clean_value(row[17].value)
                extras['preservation'] = clean_value(row[18].value)
                extras['recipient'] = clean_value(row[19].value)
                extras['storage'] = clean_value(row[20].value)
                extras['other_notes'] = clean_value(row[21].value)

                found_sample.save()

            except ObjectDoesNotExist:
                # TODO make a new one?
                pass

    return count


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog')

    opts, args = parser.parse_args()
    filename = args[0]
    loaded = import_sample_summary(filename)
    print 'updated %d samples' % loaded
