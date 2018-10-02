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

from __future__ import unicode_literals
from django.db import models
import xgds_timeseries.models as xgds_timeseries


class TempProbe(xgds_timeseries.TimeSeriesModel):
    """
    This is an auto-generated Django model created from a
    YAML specifications using ./apps/xgds_core/importer/yamlModelBuilder.py
    and YAML file ./apps/xgds_subsea_app/importer/TempProbe.yaml
    """

    timestamp = models.DateTimeField(db_index=True, null=False, blank=False)
    temperature = models.FloatField(null=True, blank=True)

    title = 'Temp Probe'
    channel_descriptions = {
                            'temperature': xgds_timeseries.ChannelDescription('Temperature', units='Celsius'),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['temperature', ]

    def __unicode__(self):
        return "%s: %s" % (self.timestamp.isoformat(), str(self.temperature))



class O2Sat(xgds_timeseries.TimeSeriesModel):
    """
    This is an auto-generated Django model created from a
    YAML specifications using ./apps/xgds_core/importer/yamlModelBuilder.py
    and YAML file ./apps/xgds_subsea_app/importer/O2S.yaml
    """

    timestamp = models.DateTimeField(db_index=True, null=False, blank=False)
    oxygen_concentration = models.FloatField(null=True, blank=True)
    oxygen_saturation = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)

    title = 'O2Sat'
    channel_descriptions = {
                            'oxygen_concentration': xgds_timeseries.ChannelDescription('Oxygen Concentration', units='microMolar'),
                            'oxygen_saturation': xgds_timeseries.ChannelDescription('Oxygen Saturation', units='percent'),
                            'temperature': xgds_timeseries.ChannelDescription('Temperature', units='Celsius'),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['oxygen_concentration', 'oxygen_saturation', 'temperature', ]

    def __unicode__(self):
        return "%s: %s %s %s" % (self.timestamp.isoformat(), str(self.oxygen_concentration), str(self.oxygen_saturation), str(self.temperature))
