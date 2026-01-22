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
from django.forms import Form
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy
from django.views.generic import FormView
from osis_parcours_doctoral_sdk.models.authorization_distribution_dto import (
    AuthorizationDistributionDTO,
)

from parcours_doctoral.contrib.enums import DecisionApprovalEnum
from parcours_doctoral.contrib.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.templatetags.parcours_doctoral import can_update_tab

__all__ = [
    'ManuscriptValidationView',
]


class ManuscriptValidationView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'manuscript-validation'
    template_name = 'parcours_doctoral/forms/manuscript_validation.html'
    extra_context = {'submit_label': gettext_lazy('Submit my decision')}
    permission_link_to_check = 'retrieve_manuscript_validation'

    @cached_property
    def authorization_distribution(self) -> AuthorizationDistributionDTO:
        return DoctorateService.get_authorization_distribution(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['authorization_distribution'] = self.authorization_distribution
        context_data['signatories'] = {
            signatory.role: signatory for signatory in self.authorization_distribution.signataires
        }
        return context_data

    def get_form_class(self):
        return (
            ManuscriptValidationApprovalForm if can_update_tab(doctorate=self.doctorate, tab=self.urlpatterns) else Form
        )

    def call_webservice(self, data):
        decision = data.pop('decision', None)

        if decision == DecisionApprovalEnum.DECLINED.name:
            DoctorateService.reject_thesis_by_lead_promoter(
                person=self.person,
                uuid=self.doctorate_uuid,
                data=data,
            )

        elif decision == DecisionApprovalEnum.APPROVED.name:
            data.pop('motif_refus', None)
            DoctorateService.accept_thesis_by_lead_promoter(
                person=self.person,
                uuid=self.doctorate_uuid,
                data=data,
            )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:manuscript-validation', pk=self.doctorate_uuid)
