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

import base64

import django
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import get_template
from django.contrib.sites.models import Site
from django.core.mail import send_mail

template = get_template('registration/password_reset_email.html')


def send_password_reset_email(user):
    token = PasswordResetTokenGenerator().make_token(user)
    site = Site.objects.get_current()
    body = template.render({'user': user, 'uid': base64.b64encode(str(user.id)), 'token': token, 'protocol':'https', 'domain':site.domain })
    send_mail(
        'Important: Register for xGDS for SUBSEA',
        body,
        'info@xgds.org',
        [user.email],
        fail_silently=False,
    )
    print 'emailed %s' % user.username


def email_users():
    users = User.objects.all()
    for user in users:
        if user.email:
            if len(user.password) < 2:
                send_password_reset_email(user)
            else:
                print 'skipped %s has password' % user.username
        else:
            print 'skipped %s no email' % user.username


if __name__ == '__main__':
    email_users()