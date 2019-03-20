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
import pandas as pd
import numpy as np
from dateutil import parser
from glob import glob
from datetime import datetime, timedelta

import django
django.setup()

from django.conf import settings

IMPORT_ROOT = os.path.join(settings.DATA_ROOT, 'incoming', settings.CRUISE_ID)
ADDENDUM_XGDS = os.path.join(IMPORT_ROOT, 'addendum', 'xgds')


def resample_file(file):
    in_file, out_file = file["in"], file["out"]
    df_names = ["ignore_a", "time", "ignore_b", "temperature"]
    df = pd.read_csv(in_file, sep="\t", header=None, names=df_names)
    df.temperature = df.temperature.astype(str)
    ignore_a = list(np.unique(df.ignore_a))[0]
    ignore_b = list(np.unique(df.ignore_b))[0]
    df = df[["time", "temperature"]]
    df.index = df.time
    df.index = [parser.parse(x) for x in df.index]
    df.temperature = [x if x.endswith("C") else None for x in df.temperature]
    df.dropna(inplace=True, subset=["temperature"])
    df.temperature = [float(x[:-1]) for x in df.temperature]
    df = df.resample('1S').mean()
    df.dropna(inplace=True, subset=["temperature"])
    df.reset_index(inplace=True)
    df.rename(index=str, columns={"index": "time"}, inplace=True)
    df.temperature = ["%.2fC" % x for x in df.temperature]
    df.time = [x.strftime("%Y-%m-%dT%H:%M:%S.000Z") for x in df.time]
    df["ignore_a"] = [ignore_a] * len(df)
    df["ignore_b"] = [ignore_b] * len(df)
    df = df[df_names]
    df.to_csv(out_file, header=False, index=False, sep="\t")


def get_list_of_files():
    list_of_files = []
    raw_files = sorted(glob(os.path.join(IMPORT_ROOT, 'raw/datalog/*_*.TEM')))

    for in_file in raw_files:
        out_file = os.path.basename(in_file)
        out_file = os.path.join(ADDENDUM_XGDS, out_file)
        assert(not out_file == in_file)
        if os.path.exists(out_file):
            print '%s already exists' % out_file
            continue
        else:
            print 'added %s' % in_file
            list_of_files.append({"in": in_file, "out": out_file})

    return list_of_files

if __name__ == '__main__':
    if not os.path.exists(ADDENDUM_XGDS):
        os.makedirs(ADDENDUM_XGDS)

    list_of_files = get_list_of_files()
    for f in list_of_files:
        print 'processing: %s' % f["in"]
        try:
            resample_file(f)
            print 'processed: %s' % f["in"]
        except Exception as e:
            print 'unable to process %s due to %s' % (f["in"], str(e))


