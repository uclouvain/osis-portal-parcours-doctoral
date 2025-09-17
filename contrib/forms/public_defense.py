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

from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.enums import ChoixLangueDefense
from parcours_doctoral.contrib.forms import (
    JPEG_MIME_TYPE,
    PNG_MIME_TYPE,
    DoctorateDateTimeField,
    DoctorateFileUploadField,
)


class PublicDefenseForm(forms.Form):
    langue = forms.ChoiceField(
        label=_('Public defence language'),
        choices=ChoixLangueDefense.choices(),
    )
    autre_langue = forms.CharField(
        label='',
        required=False,
    )
    date_heure = DoctorateDateTimeField(
        label=_('Public defence date and time'),
        help_text=_('The public defence takes place at least one month after the private defence.'),
    )
    lieu = forms.CharField(
        label=_('Public defence location'),
        help_text=_('If necessary, contact your administrator for practical arrangements.'),
        widget=forms.Textarea(attrs={'rows': '2'}),
        required=False,
    )
    local_deliberation = forms.CharField(
        label=_('Deliberation room'),
        help_text=_('If necessary, contact your administrator for practical arrangements.'),
        widget=forms.Textarea(attrs={'rows': '2'}),
        required=False,
    )
    resume_annonce = forms.CharField(
        label=_('Summary for announcement'),
        help_text=_('Please contact your administrator to draft the announcement.'),
        widget=forms.Textarea(attrs={'rows': '2'}),
        required=False,
    )
    photo_annonce = DoctorateFileUploadField(
        label=_('Photo for announcement'),
        max_files=1,
        mimetypes=[JPEG_MIME_TYPE, PNG_MIME_TYPE],
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('langue') == ChoixLangueDefense.OTHER.name:
            if not cleaned_data.get('autre_langue'):
                self.add_error('autre_langue', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['autre_langue'] = ''

        return cleaned_data
