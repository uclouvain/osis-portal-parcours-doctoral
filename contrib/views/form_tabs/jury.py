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
from django.contrib import messages
from django.forms import Form
from django.forms.models import ALL_FIELDS
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from parcours_doctoral.contrib.enums import RoleJury
from parcours_doctoral.contrib.forms.jury.membre import JuryMembreForm
from parcours_doctoral.contrib.forms.jury.preparation import JuryPreparationForm
from parcours_doctoral.contrib.views.details_tabs.jury import LoadJuryViewMixin
from parcours_doctoral.services.doctorate import (
    DoctorateJuryService,
    JuryBusinessException,
)
from parcours_doctoral.services.mixins import WebServiceFormMixin

__namespace__ = False

__all__ = [
    'JuryPreparationFormView',
    'JuryFormView',
    'JuryRequestSignaturesView',
]


class JuryPreparationFormView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/forms/jury/preparation.html'
    form_class = JuryPreparationForm
    permission_link_to_check = 'update_jury_preparation'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        return kwargs

    def get_initial(self):
        return {
            'titre_propose': self.jury.titre_propose,
            'formule_defense': self.jury.formule_defense,
            'date_indicative': self.jury.date_indicative,
            'langue_redaction': self.jury.langue_redaction,
            'langue_soutenance': self.jury.langue_soutenance,
            'commentaire': self.jury.commentaire,
        }

    def call_webservice(self, data):
        return DoctorateJuryService.modifier_jury(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )


class JuryFormView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    form_class = JuryMembreForm
    error_mapping = {
        JuryBusinessException.NonDocteurSansJustificationException: "justification_non_docteur",
        JuryBusinessException.MembreExterneSansInstitutionException: "institution",
        JuryBusinessException.MembreExterneSansPaysException: "pays",
        JuryBusinessException.MembreExterneSansNomException: "nom",
        JuryBusinessException.MembreExterneSansPrenomException: "prenom",
        JuryBusinessException.MembreExterneSansTitreException: "titre",
        JuryBusinessException.MembreExterneSansGenreException: "genre",
        JuryBusinessException.MembreExterneSansEmailException: "email",
        JuryBusinessException.MembreExterneSansLangueDeContactException: "langue",
        JuryBusinessException.MembreDejaDansJuryException: "matricule",
    }
    extra_context = {'submit_label': _('Add')}
    permission_link_to_check = 'create_jury_members'
    template_name = 'parcours_doctoral/forms/jury/jury.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'url' not in self.doctorate.links['jury_request_signatures']:
            return redirect('parcours_doctoral:jury', **self.kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        membres = self.jury.membres
        signature_conditions = DoctorateJuryService.get_signature_conditions(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

        context_data['signature_conditions'] = signature_conditions
        context_data['membres'] = (membre for membre in membres if membre.role == RoleJury.MEMBRE.name)
        context_data['membre_president'] = (membre for membre in membres if membre.role == RoleJury.PRESIDENT.name)
        context_data['membre_secretaire'] = (membre for membre in membres if membre.role == RoleJury.SECRETAIRE.name)
        context_data['add_form'] = context_data.pop('form')  # Trick template to remove save button
        return context_data

    def call_webservice(self, data):
        return DoctorateJuryService.create_jury_member(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )

    @property
    def success_url(self):
        return self.request.path


class JuryRequestSignaturesView(WebServiceFormMixin, FormView):
    urlpatterns = 'jury-request-signatures'
    form_class = Form

    def call_webservice(self, data):
        DoctorateJuryService.request_signatures(person=self.person, uuid=str(self.kwargs.get('pk')))

    def form_invalid(self, form):
        messages.error(self.request, _("There was an error while requesting signatures."))
        messages.error(self.request, '\n'.join(form.errors.get(ALL_FIELDS, [])))
        return HttpResponseRedirect(resolve_url("parcours_doctoral:update:jury", pk=self.kwargs.get('pk')))

    def get_success_url(self):
        return resolve_url("parcours_doctoral:jury", pk=self.kwargs.get('pk'))
