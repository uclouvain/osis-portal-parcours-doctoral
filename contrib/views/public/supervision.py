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

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from parcours_doctoral.contrib.enums import DecisionApprovalEnum
from parcours_doctoral.contrib.forms.supervision import DoctorateApprovalForm
from parcours_doctoral.contrib.views.public.mixins import ExternalViewMixin
from parcours_doctoral.services.doctorate import DoctorateSupervisionService, ExternalDoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__namespace__ = None

__all__ = [
    'ExternalSupervisionView',
]


class ExternalSupervisionView(ExternalViewMixin, TemplateView):
    urlpatterns = {'supervision': 'supervision/<token>'}
    template_name = 'parcours_doctoral/details/external_supervision.html'

    @cached_property
    def data(self):
        return ExternalDoctorateService.get_supervision(
            uuid=self.doctorate_uuid,
            token=self.kwargs['token'],
        ).to_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctorate'] = self.data['parcours_doctoral']
        context['supervision'] = self.data['supervision']
        return context


class DoctorateExternalApprovalView(UserPassesTestMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'external-approval': 'external-approval/<token>'}
    form_class = DoctorateApprovalForm
    template_name = 'parcours_doctoral/forms/external_supervision.html'

    def test_func(self):
        return self.request.user.is_anonymous

    @property
    def doctorate_uuid(self):
        return str(self.kwargs['pk'])

    @cached_property
    def data(self):
        return DoctorateSupervisionService.get_external_supervision(
            uuid=self.doctorate_uuid,
            token=self.kwargs['token'],
        ).to_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctorate'] = self.data['proposition']
        context['supervision'] = self.data['supervision']
        context['approval_form'] = context.pop('form')  # Trick template to remove save button
        return context

    def prepare_data(self, data):
        data["uuid_membre"] = self.kwargs.get('token')  # This is not actually used on the other side of API
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the doctorate is not approved
            data.pop('motif_refus')
        return data

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return DoctorateSupervisionService.approve_external_proposition(
                uuid=self.doctorate_uuid,
                token=self.kwargs['token'],
                **data,
            )
        return DoctorateSupervisionService.reject_external_proposition(
            uuid=self.doctorate_uuid,
            token=self.kwargs['token'],
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("Your decision has been saved."))
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:public:external-confirm',
            pk=self.kwargs['pk'],
        )


class DoctorateExternalConfirmView(TemplateView):
    urlpatterns = 'external-confirm'
    template_name = 'parcours_doctoral/forms/external_confirm.html'
