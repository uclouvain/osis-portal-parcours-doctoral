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
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect, resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView
from django.views.generic.edit import BaseFormView

from parcours_doctoral.contrib.enums import RoleJury, ChoixEtatSignature, ChoixStatutDoctorat, DecisionApprovalEnum
from parcours_doctoral.contrib.forms.jury.approvals import JuryApprovalForm, JuryApprovalByPdfForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__namespace__ = False

__all__ = [
    'JuryPreparationDetailView',
    'JuryDetailView',
    'JuryApprovalByPdfView',
    'JuryExternalResendView',
    'JuryExternalApprovalView',
    'JuryExternalConfirmView',
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
        context_data['membres'] = (membre for membre in self.jury.get('membres', []) if membre.role == RoleJury.MEMBRE.name)
        context_data['membre_president'] = (membre for membre in self.jury.get('membres', []) if membre.role == RoleJury.PRESIDENT.name)
        context_data['membre_secretaire'] = (membre for membre in self.jury.get('membres', []) if membre.role == RoleJury.SECRETAIRE.name)
        context_data['approval_form'] = context_data.pop('form')  # Trick template to remove save button
        context_data['all_approved'] = all(
            membre['signature'].get('statut') == ChoixEtatSignature.APPROVED.name
            for membre in self.jury.get('membres', [])
        )
        return context_data

    def prepare_data(self, data):
        data["uuid_membre"] = self.get_current_member_uuid()
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the admission is not approved
            data.pop('motif_refus')
        return data

    def get_current_member_uuid(self):
        return next(
            iter(
                [
                    membre['uuid']
                    for membre in self.jury['membre']
                    if self.person.global_id == membre['matricule']
                ]
            ),
            None,
        )

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return DoctorateJuryService.approve_proposition(
                person=self.person,
                uuid=self.admission_uuid,
                **data,
            )
        self.rejecting = True
        return DoctorateJuryService.reject_proposition(
            person=self.person,
            uuid=self.admission_uuid,
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("Your decision has been saved."))
        return self.request.POST.get('redirect_to') or self.request.get_full_path()


class JuryApprovalByPdfView(LoadJuryViewMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = 'approve-by-pdf'
    form_class = JuryApprovalByPdfForm

    def call_webservice(self, data):
        return DoctorateJuryService.approve_by_pdf(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:jury',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('parcours_doctoral:jury', pk=self.kwargs['pk'])


class JuryExternalResendView(LoadJuryViewMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = {'resend-invite': 'resend-invite/<uuid>'}
    template_name = 'parcours_doctoral/forms/jury/external_confirm.html'
    form_class = forms.Form

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['pk']),
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        DoctorateJuryService.resend_invite(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("An invitation has been sent again."))
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:jury',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('parcours_doctoral:jury', pk=self.kwargs['pk'])


class JuryExternalApprovalView(UserPassesTestMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'jury-external-approval': 'jury/external-approval/<token>'}
    form_class = JuryApprovalForm
    template_name = 'parcours_doctoral/forms/jury/external_approval.html'

    def test_func(self):
        return self.request.user.is_anonymous

    @cached_property
    def doctorate_uuid(self):
        return str(self.kwargs.get('pk', ''))

    @cached_property
    def data(self):
        return DoctorateJuryService.get_external_jury(
            uuid=self.doctorate_uuid,
            token=self.kwargs['token'],
        ).to_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctorate'] = self.data['parcours_doctoral']
        context['jury'] = self.data['jury']
        context['approval_form'] = context.pop('form')  # Trick template to remove save button
        return context

    def prepare_data(self, data):
        data["uuid_membre"] = self.kwargs.get('token')  # This is not actually used on the other side of API
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the admission is not approved
            data.pop('motif_refus')
        return data

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return DoctorateJuryService.approve_external_jury(
                uuid=self.doctorate_uuid,
                token=self.kwargs['token'],
                **data,
            )
        return DoctorateJuryService.reject_external_jury(
            uuid=self.doctorate_uuid,
            token=self.kwargs['token'],
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("Your decision has been saved."))
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:jury-external-confirm',
            pk=self.kwargs['pk'],
        )


class JuryExternalConfirmView(TemplateView):
    urlpatterns = {'jury-external-confirm': 'jury/external-confirm'}
    template_name = 'parcours_doctoral/forms/jury/external_confirm.html'
