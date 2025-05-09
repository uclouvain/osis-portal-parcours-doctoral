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

from django import template
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum

register = template.Library()


@register.filter
def enum_display(value, enum_name):
    if hasattr(value, "__str__"):
        # Import all needed enums
        __import__('parcours_doctoral.contrib.enums')
        for enum in ChoiceEnum.__subclasses__():
            if enum.__name__ == enum_name:
                return enum.get_value(str(value))
    return value or ''


@register.filter
def multiple_enum_display(values, enum_name):
    if values:
        # Import all needed enums
        __import__('parcours_doctoral.contrib.enums')
        for enum in ChoiceEnum.__subclasses__():
            if enum.__name__ == enum_name:
                return ", ".join([str(enum.get_value(value)) for value in values])
    return ', '.join(values)


@register.filter
def format_is_online(value):
    return _("Online") if value else _("In person")
