# __BEGIN_LICENSE__
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

from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from geocamUtil.loader import LazyGetModelByName
from geocamUtil.UserUtil import getUserByUsername
from xgds_notes2.models import LocatedNote, Role, Location


NOTE_MODEL = LazyGetModelByName(settings.XGDS_NOTES_NOTE_MODEL)


"""
Utility methods for various importers
"""


def link_sample_and_image(sample, image):
    """
    Add a note to link a sample to an image
    :param sample: the sample
    :param image: the image
    :return: the new saved note
    """
    content = 'Sample %s' % sample.name
    return add_note_to_object(content, image, sample.place)


def add_note_to_object(content, reference, place=None):
    """
    Add a note (and save it) with a generic foreign key to the reference object.
    Reference object must already be saved.
    Author will be importer.
    :param content: the body of the note
    :param reference: the reference object, ie an image
    :param place: the place to associate with the note
    :return: the new note
    """
    if not place and hasattr(reference, 'place'):
        place = reference.place

    note_dict = {'author': getUserByUsername('importer'),
                 'content': content,
                 'event_time': getattr(reference, reference.timesearchField()),
                 'event_timezone': reference.tz,
                 'creation_time': timezone.now(),
                 'position': reference.getPosition(),
                 'content_type': ContentType.objects.get_for_model(type(reference)),
                 'object_id': reference.pk,
                 'flight': reference.flight,
                 'role': Role.objects.get(value='DATA_LOGGER'),  # TODO do we need an importer role?
                 'location': Location.objects.get(value='SHIP'),
                 'place': place}
    new_note = NOTE_MODEL.get()(**note_dict)
    new_note.save()
    return new_note

