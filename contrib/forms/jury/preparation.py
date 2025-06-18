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

from parcours_doctoral.contrib.enums.jury import FormuleDefense
from parcours_doctoral.contrib.forms import (
    CustomDateInput,
    get_language_initial_choices,
)
from parcours_doctoral.contrib.forms.autocomplete import ListSelect2
from parcours_doctoral.contrib.views.autocomplete import LANGUAGE_UNDECIDED


class JuryPreparationForm(forms.Form):
    titre_propose = forms.CharField(
        label=_("Proposed thesis title"),
        help_text=_("This is a temporary title and it will be modifiable later depending on the jury analysis."),
        required=False,
    )
    formule_defense = forms.ChoiceField(
        label=_("Defense method"),
        help_text=_(
            "Refer to the specific measures of your doctoral commission to know if one of these method is "
            "mandatory to you."
        ),
        choices=FormuleDefense.choices(),
        widget=forms.RadioSelect(),
        initial=FormuleDefense.FORMULE_1.name,
        required=False,
    )
    date_indicative = forms.CharField(
        label=_("Anticipated date or period for private defence (Format 1) or admissibility (Format 2)"),
        required=False,
    )
    langue_redaction = forms.ChoiceField(
        label=_("Thesis language"),
        widget=ListSelect2(
            url="parcours_doctoral:autocomplete:language",
            attrs={
                "data-html": True,
            },
            forward=(forward.Const(True, 'show_top_languages'),),
        ),
        required=True,
    )
    langue_soutenance = forms.ChoiceField(
        label=_("Defense language"),
        widget=ListSelect2(
            url="parcours_doctoral:autocomplete:language",
            attrs={
                "data-html": True,
            },
            forward=(forward.Const(True, 'show_top_languages'),),
        ),
        required=False,
    )
    commentaire = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(),
        required=False,
    )

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the fields with dynamic choices
        lang_code = self.data.get(self.add_prefix('langue_redaction'), self.initial.get('langue_redaction'))

        if lang_code == LANGUAGE_UNDECIDED:
            choices = ((LANGUAGE_UNDECIDED, _('Undecided')),)
        else:
            choices = get_language_initial_choices(lang_code, person)

        self.fields['langue_redaction'].widget.choices = choices
        self.fields['langue_redaction'].choices = choices

        lang_code = self.data.get(self.add_prefix('langue_soutenance'), self.initial.get('langue_soutenance'))

        if lang_code == LANGUAGE_UNDECIDED:
            choices = ((LANGUAGE_UNDECIDED, _('Undecided')),)
        else:
            choices = get_language_initial_choices(lang_code, person)

        self.fields['langue_soutenance'].widget.choices = choices
        self.fields['langue_soutenance'].choices = choices
