# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import re
from copy import copy

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from osis_parcours_doctoral_sdk import OpenApiException

from base.models.person import Person
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException, api_exception_handler

INVALID_LENGTH_RE = re.compile('Invalid value for `([^`]+)`, length must be less than or equal to `([^`]+)`')


class WebServiceFormMixin:
    error_mapping = {}

    def __init__(self, *args, **kwargs):
        self._error_mapping = {exc.value: field for exc, field in self.error_mapping.items()}
        self.error_message = _("Please correct the errors below")
        super().__init__(*args, **kwargs)

    def prepare_data(self, data):
        return data

    def form_invalid(self, form):
        # On error, display global message
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)

    def handle_form_exception(self, form, exception):
        if exception.status_code in self._error_mapping:
            form.add_error(self._error_mapping[exception.status_code], exception.detail)
        else:
            form.add_error(None, exception.detail)

    def form_valid(self, form):
        data = self.prepare_data(copy(form.cleaned_data))

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:
            for exception in multiple_business_api_exception.exceptions:
                self.handle_form_exception(form, exception)
            return self.form_invalid(form)
        except PermissionDenied as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except OpenApiException as e:
            # We try to be smart about the error
            invalid_length = INVALID_LENGTH_RE.match(str(e))
            if invalid_length is not None and invalid_length.group(1) in form.fields:
                form.add_error(
                    invalid_length.group(1),
                    _("This field must be less that {length} characters.").format(length=invalid_length.group(2)),
                )
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
        return super().form_valid(form)

    def call_webservice(self, data):
        raise NotImplementedError

    def get_success_url(self):
        messages.info(self.request, _("Your data have been saved"))

        # If a url to redirect is specified in the request, use it
        if self.request.POST.get('redirect_to'):
            return self.request.POST.get('redirect_to')

        if self.success_url:
            return self.success_url

        # Redirect on detail
        return self._get_url(self.request.resolver_match.url_name)

    @property
    def person(self) -> Person:
        return self.request.user.person


class ServiceMeta(type):
    """
    A metaclass that decorates all class methods with exception handler.

    'api_exception_cls' must be specified as attribute
    """

    def __new__(mcs, name, bases, attrs):
        if 'api_exception_cls' not in attrs:
            raise AttributeError("{name} must declare 'api_exception_cls' attribute".format(name=name))
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, classmethod):
                attrs[attr_name] = classmethod(api_exception_handler(attrs['api_exception_cls'])(attr_value.__func__))
        return super().__new__(mcs, name, bases, attrs)
