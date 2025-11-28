# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.contrib.forms import (
    CustomDateInput,
    DoctorateDateTimeField,
    DoctorateFileUploadField,
)


class PrivateDefenseForm(forms.Form):
    titre_these = forms.CharField(
        label=_('Thesis title'),
        max_length=255,
    )

    date_heure_defense_privee = DoctorateDateTimeField(
        label=_('Private defence date and time'),
        help_text=_(
            'The private defence date is chosen collectively by the jury and in agreement with the PhD student'
        ),
    )

    lieu_defense_privee = forms.CharField(
        label=_('Private defence location'),
        help_text=_('If necessary, contact your administrator for practical arrangements.'),
        required=False,
        max_length=255,
    )

    date_envoi_manuscrit = forms.DateField(
        label=_('Date of manuscript submission to the thesis exam board'),
        widget=CustomDateInput,
        required=False,
    )


class PromoterPrivateDefenseForm(forms.Form):
    proces_verbal_defense_privee = DoctorateFileUploadField(
        label=_('Private defence minutes'),
        help_text=_('The minutes will be uploaded by the thesis exam board secretary or chair.'),
        required=False,
    )
