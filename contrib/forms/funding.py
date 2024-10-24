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

from django import forms
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.contrib.enums.financement import (
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from parcours_doctoral.contrib.forms import (
    autocomplete,
    CustomDateInput,
    EMPTY_CHOICE,
    SelectOrOtherField,
    get_scholarship_choices,
    DoctorateFileUploadField as FileUploadField,
    RadioBooleanField,
)
from parcours_doctoral.utils import mark_safe_lazy


class FundingForm(forms.Form):
    type = forms.ChoiceField(
        label=_("Current funding"),
        choices=EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        help_text=_(
            "If you don't have any funding yet, please choose \"Self-funding\" and explain the"
            " considered funding in the \"Comment\" area."
        ),
    )
    type_contrat_travail = SelectOrOtherField(
        label=_("Work contract type"),
        choices=EMPTY_CHOICE + ChoixTypeContratTravail.choices(),
        required=False,
        help_text=_("Specify employer and function"),
    )
    eft = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Full-time equivalent (as %)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    bourse_recherche = forms.CharField(
        label=_("Research scholarship"),
        required=False,
        widget=autocomplete.ListSelect2(
            url='parcours_doctoral:autocomplete:scholarship',
        ),
    )
    autre_bourse_recherche = forms.CharField(
        label=_("If other scholarship, specify"),
        required=False,
        max_length=255,
    )
    bourse_date_debut = forms.DateField(
        label=_("Scholarship start date"),
        widget=CustomDateInput(),
        required=False,
    )
    bourse_date_fin = forms.DateField(
        label=_("Scholarship end date"),
        widget=CustomDateInput(),
        required=False,
        help_text=_("Scholarship end date prior to any possible renewal."),
    )
    bourse_preuve = FileUploadField(
        label=_("Proof of scholarship"),
        required=False,
        help_text=_(
            "For example, a contract, a letter from a supervisor, or any other document showing that you have been "
            "awarded the scholarship on the dates indicated."
        ),
    )
    duree_prevue = forms.IntegerField(
        label=_("Estimated time to complete the PhD (in months)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    temps_consacre = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Time allocated for thesis (in %)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    est_lie_fnrs_fria_fresh_csc = RadioBooleanField(
        label=_("Is your admission request linked with a FNRS, FRIA, FRESH or CSC application?"),
        required=False,
        initial=False,
        help_text=mark_safe_lazy(
            _(
                "<a href='https://uclouvain.be/en/research/valodoc/confirmation-eligibility-doctoral-programme.html' "
                "target='_blank'>"
                "https://uclouvain.be/en/research/valodoc/confirmation-eligibility-doctoral-programme.html"
                "</a>"
            ),
        ),
    )
    commentaire = forms.CharField(
        label=_("Comment"),
        required=False,
        widget=forms.Textarea,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        self.person = getattr(self, 'person', kwargs.pop('person', None))

        super().__init__(*args, **kwargs)

        scholarship_uuid = self.data.get(self.add_prefix('bourse_recherche'), self.initial.get('bourse_recherche'))
        if scholarship_uuid:
            self.fields['bourse_recherche'].widget.choices = get_scholarship_choices(
                uuid=scholarship_uuid,
                person=self.person,
            )

        # Initialize some fields if they are not already set in the input data
        for field in [
            'est_lie_fnrs_fria_fresh_csc',
        ]:
            if self.initial.get(field) in {None, ''}:
                self.initial[field] = self.fields[field].initial

    def clean(self):
        data = super().clean()

        # Some consistency checks
        if data.get('type') == ChoixTypeFinancement.WORK_CONTRACT.name:
            if not data.get('type_contrat_travail'):
                self.add_error('type_contrat_travail', _("This field is required."))

            if not data.get('eft'):
                self.add_error('eft', _("This field is required."))

        elif data.get('type') == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            if data.get('bourse_recherche'):
                data['autre_bourse_recherche'] = ''
            elif data.get('autre_bourse_recherche'):
                data['bourse_recherche'] = ''
            else:
                self.add_error('bourse_recherche', _('This field is required.'))
                self.add_error('autre_bourse_recherche', '')

        return data
