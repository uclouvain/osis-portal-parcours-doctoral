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
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.views.generic import TemplateView, FormView

from parcours_doctoral.contrib.enums import RoleJury, ChoixEtatSignature, ChoixStatutDoctorat
from parcours_doctoral.contrib.forms.jury.approvals import JuryApprovalForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__namespace__ = False

__all__ = [
    'JuryPreparationDetailView',
    'JuryDetailView',
]


class LoadJuryViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    @cached_property
    def jury(self):
        return DoctorateJuryService.retrieve_jury(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        return context


class JuryPreparationDetailView(LoadJuryViewMixin, TemplateView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/details/jury/preparation.html'
    permission_link_to_check = 'retrieve_jury_preparation'


class JuryDetailView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury'
    template_name = 'parcours_doctoral/forms/jury/jury.html'
    permission_link_to_check = 'list_jury_members'
    form_class = JuryApprovalForm

    def get(self, request, *args, **kwargs):
        # If not signing in progress and ability to update jury, redirect on update page
        if (
            self.doctorate.statut == ChoixStatutDoctorat.CONFIRMATION_REUSSIE.name
            and 'url' in self.doctorate.links['request_signatures']
        ):
            return redirect('parcours_doctoral:update:jury', **self.kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        membres = DoctorateJuryService.list_jury_members(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )
        context_data['membres'] = (membre for membre in membres if membre.role == RoleJury.MEMBRE.name)
        context_data['membre_president'] = (membre for membre in membres if membre.role == RoleJury.PRESIDENT.name)
        context_data['membre_secretaire'] = (membre for membre in membres if membre.role == RoleJury.SECRETAIRE.name)
        context_data['approval_form'] = context_data.pop('form')  # Trick template to remove save button
        context_data['all_approved'] = all(
            signature.get('statut') == ChoixEtatSignature.APPROVED.name
            for signature in self.jury.get('signatures', [])
        )
        return context_data
    #
    # def prepare_data(self, data):
    #     data["uuid_membre"] = self.get_current_member_uuid()
    #     if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
    #         # The reason is useful only if the admission is not approved
    #         data.pop('motif_refus')
    #     return data
    #
    # def get_current_member_uuid(self):
    #     return next(
    #         iter(
    #             [
    #                 signature['promoteur']['uuid']
    #                 for signature in self.supervision['signatures_promoteurs']
    #                 if self.person.global_id == signature['promoteur']['matricule']
    #             ]
    #             + [
    #                 signature['membre_ca']['uuid']
    #                 for signature in self.supervision['signatures_membres_ca']
    #                 if self.person.global_id == signature['membre_ca']['matricule']
    #             ]
    #         ),
    #         None,
    #     )
    #
    # def call_webservice(self, data):
    #     decision = data.pop('decision')
    #     if decision == DecisionApprovalEnum.APPROVED.name:
    #         return AdmissionSupervisionService.approve_proposition(
    #             person=self.person,
    #             uuid=self.admission_uuid,
    #             **data,
    #         )
    #     self.rejecting = True
    #     return AdmissionSupervisionService.reject_proposition(
    #         person=self.person,
    #         uuid=self.admission_uuid,
    #         **data,
    #     )
    #
    # def get_success_url(self):
    #     messages.info(self.request, _("Your decision has been saved."))
    #     if (
    #         self.person.global_id
    #         in [signature['membre_ca']['matricule'] for signature in self.supervision['signatures_membres_ca']]
    #         and self.rejecting
    #     ):
    #         try:
    #             AdmissionPropositionService().get_supervised_propositions(self.request.user.person)
    #         except PermissionDenied:
    #             # That may be the last admission the member has access to, if so, redirect to homepage
    #             return resolve_url('home')
    #         # Redirect on list
    #         return resolve_url('admission:supervised-list')
    #     return self.request.POST.get('redirect_to') or self.request.get_full_path()
