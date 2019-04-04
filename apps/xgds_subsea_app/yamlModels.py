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
from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class TempProbe(xgds_timeseries.TimeSeriesModel):
    """
    This is an auto-generated Django model created from a
    YAML specifications using ./apps/xgds_core/importer/yamlModelBuilder.py
    and YAML file ./apps/xgds_subsea_app/importer/TempProbe.yaml
    """

    timestamp = models.DateTimeField(db_index=True, null=False, blank=False)
    temperature = models.FloatField(null=True, blank=True)
    flight = models.ForeignKey('xgds_core.Flight', on_delete=models.SET_NULL, blank=True, null=True)

    title = 'Temp Probe'
    channel_descriptions = {
                            'temperature': xgds_timeseries.ChannelDescription('Temp', units='C'),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['temperature', ]

    def __unicode__(self):
        return "%s: %s" % (self.timestamp.isoformat(), str(self.temperature))


# if settings.XGDS_CORE_REDIS and settings.XGDS_SSE:
#     @receiver(post_save, sender=TempProbe)
#     def publishAfterSave(sender, instance, **kwargs):
#         for channel in settings.XGDS_SSE_TEMP_PROBE_CHANNELS:
#             publishRedisSSE(channel, settings.XGDS_TEMP_PROBE_SSE_TYPE.lower(),
#                             json.dumps(instance.toDict(), cls=DatetimeJsonEncoder))


class ConductivityTempDepth(xgds_timeseries.TimeSeriesModel):
    """
    This is an auto-generated Django model created from a
    YAML specifications using ./apps/xgds_core/importer/yamlModelBuilder.py
    and YAML file ./apps/xgds_subsea_app/importer/CTD.yaml
    """

    timestamp = models.DateTimeField(db_index=True, null=False, blank=False)
    temperature = models.FloatField(null=True, blank=True)
    conductivity = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    salinity = models.FloatField(null=True, blank=True)
    sound_velocity = models.FloatField(null=True, blank=True)
    flight = models.ForeignKey('xgds_core.Flight', on_delete=models.SET_NULL, blank=True, null=True)

    title = 'Conductivity Temp Depth'
    channel_descriptions = {
                            'temperature': xgds_timeseries.ChannelDescription('Temp', units='C'),
                            'conductivity': xgds_timeseries.ChannelDescription('Conductivity', units='S/m'),
                            'pressure': xgds_timeseries.ChannelDescription('Pressure', units='decibars'),
                            'salinity': xgds_timeseries.ChannelDescription('Salinity', units='psu'),
                            'sound_velocity': xgds_timeseries.ChannelDescription('Sound Velocity', units='m/s'),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['temperature', 'conductivity', 'pressure', 'salinity', 'sound_velocity', ]

    def __unicode__(self):
        return "%s: %s %s %s %s %s" % (self.timestamp.isoformat(), str(self.temperature), str(self.conductivity), str(self.pressure), str(self.salinity), str(self.sound_velocity))

# @receiver(post_save, sender=ConductivityTempDepth)
# def publishAfterSave(sender, instance, **kwargs):
#     if settings.XGDS_CORE_REDIS:
#         for channel in settings.XGDS_SSE_COND_TEMP_DEPTH_CHANNELS:
#             publishRedisSSE(channel, settings.XGDS_COND_TEMP_DEPTH_SSE_TYPE.lower(),
#                             json.dumps(instance.toDict(), cls=DatetimeJsonEncoder))

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
    flight = models.ForeignKey('xgds_core.Flight', on_delete=models.SET_NULL, blank=True, null=True)

    title = 'O2Sat'
    channel_descriptions = {
                            'oxygen_concentration': xgds_timeseries.ChannelDescription('O2 Conc', units='microMolar'),
                            'oxygen_saturation': xgds_timeseries.ChannelDescription('O2 Sat', units='%'),
                            'temperature': xgds_timeseries.ChannelDescription('O2 Temp', units='C'),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['oxygen_concentration', 'oxygen_saturation', 'temperature', ]

    def __unicode__(self):
        return "%s: %s %s %s" % (self.timestamp.isoformat(), str(self.oxygen_concentration), str(self.oxygen_saturation), str(self.temperature))

# @receiver(post_save, sender=O2Sat)
# def publishAfterSave(sender, instance, **kwargs):
#     if settings.XGDS_CORE_REDIS:
#         for channel in settings.XGDS_SSE_O2_SAT_CHANNELS:
#             publishRedisSSE(channel, settings.XGDS_O2_SAT_SSE_TYPE.lower(),
#                             json.dumps(instance.toDict(), cls=DatetimeJsonEncoder))