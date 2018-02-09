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

from django.contrib import admin
from basaltApp.models import *  # pylint: disable=W0401

class BasaltInstrumentDataProductAdmin(admin.ModelAdmin):
    raw_id_fields = ("location",)

class BasaltImageSetAdmin(admin.ModelAdmin):
    raw_id_fields = ("track_position", "exif_position", "user_position")

admin.site.register(BasaltResource)
admin.site.register(CurrentPosition)
admin.site.register(PastPosition)
admin.site.register(EV)
admin.site.register(BasaltPlanExecution)
admin.site.register(BasaltSample)
admin.site.register(DataType)
admin.site.register(BasaltActiveFlight)
admin.site.register(BasaltFlight)
admin.site.register(ScienceInstrument)
# admin.site.register(AsdDataProduct, BasaltInstrumentDataProductAdmin)
# admin.site.register(FtirDataProduct, BasaltInstrumentDataProductAdmin)
# admin.site.register(PxrfDataProduct, BasaltInstrumentDataProductAdmin)
admin.site.register(FtirSample)
admin.site.register(AsdSample)
admin.site.register(BasaltSingleImage)
admin.site.register(BasaltImageSet, BasaltImageSetAdmin)
admin.site.register(ActivityStatus)
admin.site.register(BasaltCondition)
admin.site.register(BasaltConditionHistory)
