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
from django.contrib.postgres.forms import SimpleArrayField
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.contrib.enums.authorization_distribution import (
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.contrib.forms import (
    EMPTY_CHOICE,
    CustomDateInput,
    get_language_initial_choices,
)
from parcours_doctoral.contrib.forms.autocomplete import ListSelect2, TagSelect2
from parcours_doctoral.contrib.views.autocomplete import LANGUAGE_UNDECIDED


class AuthorizationDistributionForm(forms.Form):
    sources_financement = forms.CharField(
        label=_('Sources of funding throughout PhD'),
        required=False,
        max_length=100,
    )

    resume_anglais = forms.CharField(
        label=_('Summary in English'),
        required=False,
        max_length=100,
    )

    resume_autre_langue = forms.CharField(
        label=_('Summary in other language'),
        required=False,
        max_length=100,
    )

    langue_redaction_these = forms.ChoiceField(
        label=_('Thesis language'),
        widget=ListSelect2(
            url='parcours_doctoral:autocomplete:language',
            attrs={
                'data-html': True,
            },
            forward=(forward.Const(True, 'show_top_languages'),),
        ),
        required=False,
    )

    mots_cles = SimpleArrayField(
        base_field=forms.CharField(max_length=50),
        label=_('Keywords'),
        required=False,
        widget=TagSelect2(
            attrs={
                'data-minimum-input-length': 1,
            },
        ),
    )

    type_modalites_diffusion = forms.ChoiceField(
        label=_('Distribution conditions'),
        required=False,
        choices=EMPTY_CHOICE + TypeModalitesDiffusionThese.choices(),
        help_text=_(
            'Access to the digital thesis may be open to the entire world, limited to the UCLouvain intranet or '
            'reserved solely for administrators. Access may also be blocked for a specific period of time, if the '
            'author prefers paper distribution for a certain period of time (e.g. two or three years).'
        ),
    )

    date_embargo = forms.DateField(
        label=_('End of the embargo period'),
        required=False,
        widget=CustomDateInput,
        help_text=_('At the end of the embargo period, the thesis becomes public.'),
    )

    limitations_additionnelles_chapitres = forms.CharField(
        label=_('Additional limitation for certain specific chapters'),
        required=False,
        widget=forms.Textarea,
        help_text=_(
            'Access may be restricted to certain parts of the thesis, for example to protect parts covered by '
            'confidentiality. Please specify this in this text area, mentioning the protected chapters and the '
            'type of access (restricted, forbidden, or embargo and date).'
        ),
    )

    accepter_conditions = forms.BooleanField(
        label=_('I accept'),
        required=False,
    )

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the fields with dynamic choices
        lang_code = self.data.get(self.add_prefix('langue_redaction_these'), self.initial.get('langue_redaction_these'))
        self.fields['langue_redaction_these'].choices = get_language_initial_choices(lang_code, person)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('langue_redaction_these') == LANGUAGE_UNDECIDED:
            self.add_error('langue_redaction_these', _('Please select a language.'))

        if cleaned_data.get('type_modalites_diffusion') != TypeModalitesDiffusionThese.ACCES_EMBARGO.name:
            cleaned_data['date_embargo'] = None

        return cleaned_data
