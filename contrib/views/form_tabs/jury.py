# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from parcours_doctoral.contrib.enums import RoleJury
from parcours_doctoral.contrib.forms.jury.membre import JuryMembreForm
from parcours_doctoral.contrib.forms.jury.preparation import JuryPreparationForm
from parcours_doctoral.contrib.views.details_tabs.jury import LoadJuryViewMixin, JuryDetailView
from parcours_doctoral.services.doctorate import DoctorateJuryService, JuryBusinessException
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
        JuryBusinessException.MembreDejaDansJuryException: "matricule",
    }
    extra_context = {'submit_label': _('Add')}
    permission_link_to_check = 'create_jury_members'
    template_name = 'parcours_doctoral/forms/jury/jury.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'url' not in self.doctorate.links['request_signatures']:
            return redirect('parcours_doctoral:jury', **self.kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        membres = DoctorateJuryService.list_jury_members(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )
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


class JuryRequestSignaturesView(LoginRequiredMixin, SuccessMessageMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury-request-signatures'
    form_class = Form
    success_message = _("Signature requests sent")

    def call_webservice(self, data):
        DoctorateJuryService.request_signatures(person=self.person, uuid=str(self.kwargs.get('pk')))

    def form_invalid(self, form):
        messages.error(self.request, _("Please first correct the errors"))
        return HttpResponseRedirect(resolve_url("parcours_doctoral:update:jury", pk=self.kwargs.get('pk')))

    def get_success_url(self):
        return resolve_url("parcours_doctoral:jury", pk=self.kwargs.get('pk'))




# class DoctorateAdmissionApprovalByPdfView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
#     urlpatterns = 'approve-by-pdf'
#     form_class = DoctorateAdmissionApprovalByPdfForm
#
#     def call_webservice(self, data):
#         return AdmissionSupervisionService.approve_by_pdf(
#             person=self.person,
#             uuid=str(self.kwargs['pk']),
#             **data,
#         )
#
#     def get_success_url(self):
#         return self.request.POST.get('redirect_to') or resolve_url(
#             'admission:doctorate:supervision',
#             pk=self.kwargs['pk'],
#         )
#
#     def form_invalid(self, form):
#         return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])
#
#
# class DoctorateAdmissionExternalResendView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
#     urlpatterns = {'resend-invite': 'resend-invite/<uuid>'}
#     template_name = 'admission/doctorate/forms/external_confirm.html'
#     form_class = forms.Form
#
#     def prepare_data(self, data):
#         return {
#             'uuid_proposition': str(self.kwargs['pk']),
#             'uuid_membre': self.kwargs['uuid'],
#         }
#
#     def call_webservice(self, data):
#         AdmissionSupervisionService.resend_invite(
#             person=self.person,
#             uuid=str(self.kwargs['pk']),
#             **data,
#         )
#
#     def get_success_url(self):
#         messages.info(self.request, _("An invitation has been sent again."))
#         return self.request.POST.get('redirect_to') or resolve_url(
#             'admission:doctorate:supervision',
#             pk=self.kwargs['pk'],
#         )
#
#     def form_invalid(self, form):
#         return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])
