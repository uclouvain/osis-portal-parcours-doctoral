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
from dal import forward
from django import forms
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.contrib.forms import (
    JPEG_MIME_TYPE,
    PNG_MIME_TYPE,
    DoctorateDateTimeField,
    DoctorateFileUploadField,
    get_language_initial_choices,
)
from parcours_doctoral.contrib.forms.autocomplete import ListSelect2
from parcours_doctoral.contrib.views.autocomplete import LANGUAGE_UNDECIDED


class PublicDefenseForm(forms.Form):
    langue_soutenance_publique = forms.ChoiceField(
        label=_('Public defence language'),
        widget=ListSelect2(
            url="parcours_doctoral:autocomplete:language",
            attrs={
                "data-html": True,
            },
            forward=(forward.Const(True, 'show_top_languages'),),
        ),
    )
    date_heure_soutenance_publique = DoctorateDateTimeField(
        label=_('Public defence date and time'),
        help_text=_('The public defence takes place at least one month after the private defence.'),
    )
    lieu_soutenance_publique = forms.CharField(
        label=_('Public defence location'),
        help_text=_('If necessary, contact your administrator for practical arrangements.'),
        required=False,
        max_length=255,
    )
    local_deliberation = forms.CharField(
        label=_('Deliberation room'),
        help_text=_('If necessary, contact your administrator for practical arrangements.'),
        required=False,
        max_length=255,
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

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lang_code = self.data.get(
            self.add_prefix('langue_soutenance_publique'),
            self.initial.get('langue_soutenance_publique'),
        )
        self.fields['langue_soutenance_publique'].choices = get_language_initial_choices(lang_code, person)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('langue_soutenance_publique') == LANGUAGE_UNDECIDED:
            self.add_error('langue_soutenance_publique', _('Please select a language.'))

        return cleaned_data


class PromoterPublicDefenseForm(forms.Form):
    proces_verbal_soutenance_publique = DoctorateFileUploadField(
        label=_('Public defence minutes'),
        help_text=_('The minutes will be uploaded by the thesis exam board secretary or chair.'),
        required=False,
    )
