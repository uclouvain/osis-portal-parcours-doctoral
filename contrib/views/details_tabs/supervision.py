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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.edit import BaseFormView
from osis_parcours_doctoral_sdk import ApiException

from parcours_doctoral.contrib.enums import ActorType, DecisionApprovalEnum
from parcours_doctoral.contrib.forms.supervision import DoctorateApprovalForm, DoctorateApprovalByPdfForm
from parcours_doctoral.contrib.forms.supervision import (
    DoctorateMemberSupervisionForm,
)
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.doctorate import DoctorateSupervisionService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = [
    'SupervisionDetailView',
]
__namespace__ = False


class SupervisionDetailView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'supervision'
    template_name = 'parcours_doctoral/details/supervision.html'
    permission_link_to_check = 'retrieve_supervision'
    form_class = DoctorateApprovalForm
    rejecting = False

    @cached_property
    def supervision(self):
        return DoctorateService.get_supervision(
            person=self.person,
            uuid_doctorate=self.doctorate_uuid,
        ).to_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supervision'] = self.supervision
        context['approve_by_pdf_form'] = DoctorateApprovalByPdfForm()
        context['approval_form'] = context.pop('form')  # Trick template to remove save button
        return context

    def get_initial(self):
        return {
            'institut_these': self.doctorate.projet.institut_these,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['include_institut_these'] = (
            # User is the reference promoter
            self.get_current_member_uuid() == self.supervision['promoteur_reference']
            # institut_these is not yet set
            and not self.doctorate.projet.institut_these
        )
        return kwargs

    def prepare_data(self, data):
        data["uuid_membre"] = self.get_current_member_uuid()
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the doctorate is not approved
            data.pop('motif_refus')
        return data

    def get_current_member_uuid(self):
        return next(
            iter(
                [
                    signature['promoteur']['uuid']
                    for signature in self.supervision['signatures_promoteurs']
                    if self.person.global_id == signature['promoteur']['matricule']
                ]
                + [
                    signature['membre_ca']['uuid']
                    for signature in self.supervision['signatures_membres_ca']
                    if self.person.global_id == signature['membre_ca']['matricule']
                ]
            ),
            None,
        )

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return DoctorateSupervisionService.approve_proposition(
                person=self.person,
                uuid=self.doctorate_uuid,
                **data,
            )
        self.rejecting = True
        return DoctorateSupervisionService.reject_proposition(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("Your decision has been saved."))
        if (
            self.person.global_id
            in [signature['membre_ca']['matricule'] for signature in self.supervision['signatures_membres_ca']]
            and self.rejecting
        ):
            try:
                DoctorateService().get_supervised_propositions(self.request.user.person)
            except PermissionDenied:
                # That may be the last doctorate the member has access to, if so, redirect to homepage
                return resolve_url('home')
            # Redirect on list
            return resolve_url('parcours_doctoral:supervised-list')
        return self.request.POST.get('redirect_to') or self.request.get_full_path()


class DoctorateRemoveActorView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'remove-actor': 'remove-member/<type>/<uuid>'}
    form_class = forms.Form
    template_name = 'parcours_doctoral/forms/remove_actor.html'
    actor_type_mapping = {
        ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
        ActorType.CA_MEMBER.name: ('signatures_membres_ca', 'membre_ca'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            supervision = DoctorateService.get_supervision(
                person=self.person,
                uuid_doctorate=self.doctorate_uuid,
            ).to_dict()
            context['member'] = self.get_member(supervision)
        except (ApiException, AttributeError, KeyError):
            raise Http404(_('Member not found'))
        return context

    def get_member(self, supervision):
        collection_name, attr_name = self.actor_type_mapping[self.kwargs['type']]
        for signature in supervision[collection_name]:
            member = signature[attr_name]
            if member['uuid'] == self.kwargs['uuid']:
                return member
        raise KeyError

    def prepare_data(self, data):
        return {
            'type': self.kwargs['type'],
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        DoctorateSupervisionService.remove_member(person=self.person, uuid=self.doctorate_uuid, **data)

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or self._get_url("supervision")


class DoctorateEditExternalMemberView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'edit-external-member': 'edit-external-member/<uuid>'}
    form_class = DoctorateMemberSupervisionForm

    def prepare_data(self, data):
        return {'uuid_proposition': self.doctorate_uuid, 'uuid_membre': self.kwargs['uuid'], **data}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        kwargs['prefix'] = f"member-{self.kwargs['uuid']}"
        return kwargs

    def call_webservice(self, data):
        DoctorateSupervisionService.edit_external_member(person=self.person, uuid=self.doctorate_uuid, **data)

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or self._get_url("supervision")

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below"))
        messages.error(self.request, str(form.errors))
        return redirect('parcours_doctoral:supervision', pk=self.kwargs['pk'])


class DoctorateSetReferencePromoterView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = {'set-reference-promoter': 'set-reference-promoter/<uuid>'}
    form_class = forms.Form

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['pk']),
            'uuid_promoteur': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        DoctorateSupervisionService.set_reference_promoter(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:supervision',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('parcours_doctoral:supervision', pk=self.kwargs['pk'])


class DoctorateApprovalByPdfView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = 'approve-by-pdf'
    form_class = DoctorateApprovalByPdfForm

    def call_webservice(self, data):
        return DoctorateSupervisionService.approve_by_pdf(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:supervision',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('parcours_doctoral:supervision', pk=self.kwargs['pk'])


class DoctorateExternalResendView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = {'resend-invite': 'resend-invite/<uuid>'}
    template_name = 'parcours_doctoral/forms/external_confirm.html'
    form_class = forms.Form

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['pk']),
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        DoctorateSupervisionService.resend_invite(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("An invitation has been sent again."))
        return self.request.POST.get('redirect_to') or resolve_url(
            'parcours_doctoral:supervision',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('parcours_doctoral:supervision', pk=self.kwargs['pk'])
