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
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from base.models.person import Person
from base.models.utils.utils import ChoiceEnum
from parcours_doctoral.contrib.enums import GenreMembre, TitreMembre
from parcours_doctoral.contrib.forms import EMPTY_CHOICE, autocomplete


class JuryMembreForm(forms.Form):
    class InstitutionPrincipaleChoices(ChoiceEnum):
        UCL = _('UCLouvain')
        OTHER = _('Other')

    matricule = forms.CharField(
        label=_('Lookup somebody'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:person",
            attrs={
                'data-placeholder': _('Last name / First name / Global id'),
            },
        ),
    )

    institution_principale = forms.ChoiceField(
        label=_("Main institute"),
        choices=InstitutionPrincipaleChoices.choices(),
        widget=forms.RadioSelect(),
        initial=InstitutionPrincipaleChoices.UCL.name,
        required=True,
    )

    institution = forms.CharField(
        label=_("Specify if other"),
        required=False,
    )

    autre_institution = forms.CharField(
        label=_("Other institute (if necessary)"),
        required=False,
    )

    pays = forms.CharField(
        label=_('Country'),
        widget=autocomplete.ListSelect2(
            url='parcours_doctoral:autocomplete:country',
            attrs={
                "data-html": True,
            },
        ),
        required=False,
    )

    nom = forms.CharField(
        label=_("Surname"),
        required=False,
    )

    prenom = forms.CharField(
        label=_("First name"),
        required=False,
    )

    titre = forms.ChoiceField(
        label=pgettext_lazy("jury", "Title"),
        choices=TitreMembre.choices(),
        required=False,
    )

    justification_non_docteur = forms.CharField(
        label=_("Justification"),
        widget=forms.Textarea(),
        required=False,
    )

    genre = forms.ChoiceField(
        label=_("Gender"),
        choices=GenreMembre.choices(),
        required=False,
    )

    langue = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=EMPTY_CHOICE + tuple(settings.LANGUAGES),
        initial=settings.LANGUAGE_CODE,
    )

    email = forms.EmailField(
        label=pgettext_lazy("doctorate", "Email"),
        required=False,
    )

    langue = forms.ChoiceField(
        label=_("Contact language"),
        help_text=_("Language in which the domain doctoral committee can contact this person"),
        required=False,
        choices=EMPTY_CHOICE + tuple(settings.LANGUAGES),
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pays = self.initial.get('pays', None)
        if pays:
            self.fields['pays'].widget.choices = EMPTY_CHOICE + ((pays, pays.name),)
        matricule = self.initial.get('matricule', None)
        if matricule:
            person = Person.objects.get(global_id=matricule)
            self.fields['matricule'].widget.choices = EMPTY_CHOICE + ((matricule, str(person)),)

    def clean(self):
        cleaned_data = super().clean()

        main_institution = cleaned_data.pop('institution_principale')

        if main_institution == self.InstitutionPrincipaleChoices.UCL.name:
            if not cleaned_data.get('matricule'):
                self.add_error('matricule', _("Please select a member"))

        return cleaned_data
