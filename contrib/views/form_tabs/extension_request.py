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
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from osis_parcours_doctoral_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO

from parcours_doctoral.contrib.enums import ChoixStatutDoctorat
from parcours_doctoral.contrib.forms.extension_request import ExtensionRequestForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['ExtensionRequestFormView']


class ExtensionRequestFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/extension_request.html'
    form_class = ExtensionRequestForm
    extra_context = {'submit_label': _('Submit my new deadline')}
    permission_link_to_check = 'update_confirmation_extension'

    def dispatch(self, request, *args, **kwargs):
        if (
            self.doctorate.statut != ChoixStatutDoctorat.ADMIS.name
            and self.doctorate.statut != ChoixStatutDoctorat.CONFIRMATION_SOUMISE.name
        ):
            return redirect("parcours_doctoral:extension-request", uuid=self.doctorate_uuid)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def confirmation_paper(self) -> ConfirmationPaperDTO:
        return DoctorateService.get_last_confirmation_paper(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_initial(self):
        return (
            {
                'nouvelle_echeance': self.confirmation_paper.demande_prolongation['nouvelle_echeance'],
                'justification_succincte': self.confirmation_paper.demande_prolongation['justification_succincte'],
                'lettre_justification': self.confirmation_paper.demande_prolongation['lettre_justification'],
            }
            if self.confirmation_paper and self.confirmation_paper.demande_prolongation
            else {}
        )

    def call_webservice(self, data):
        DoctorateService.submit_confirmation_paper_extension_request(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )
