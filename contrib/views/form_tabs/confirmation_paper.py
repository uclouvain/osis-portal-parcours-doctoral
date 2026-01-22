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
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import FormView
from osis_parcours_doctoral_sdk.models.confirmation_paper_dto import ConfirmationPaperDTO

from parcours_doctoral.contrib.forms.confirmation_paper import (
    ConfirmationPaperForm,
    PromoterConfirmationPaperForm,
)
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import (
    ConfirmationPaperBusinessException,
    DoctorateService,
)
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['ConfirmationPaperFormView']


class ConfirmationPaperFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'confirmation-paper': 'confirmation'}
    error_mapping = {
        ConfirmationPaperBusinessException.EpreuveConfirmationDateIncorrecteException: 'date',
    }

    @property
    def permission_link_to_check(self):
        return 'update_confirmation' if self.is_doctorate_student else 'upload_pdf_confirmation'

    @cached_property
    def confirmation_paper(self) -> ConfirmationPaperDTO:
        return DoctorateService.get_last_confirmation_paper(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_template_names(self):
        if self.is_doctorate_student:
            return 'parcours_doctoral/forms/confirmation_papers.html'
        else:
            return 'parcours_doctoral/forms/promoter_confirmation_papers.html'

    def get_form_class(self):
        if self.is_doctorate_student:
            return ConfirmationPaperForm
        else:
            return PromoterConfirmationPaperForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['confirmation_paper'] = self.confirmation_paper

        if self.is_doctorate_student:
            context_data['submit_label'] = _('Submit and notify CDD')

        return context_data

    def get_initial(self):
        return (
            {
                'date': self.confirmation_paper.date,
                'rapport_recherche': self.confirmation_paper.rapport_recherche,
                'proces_verbal_ca': self.confirmation_paper.proces_verbal_ca,
                'avis_renouvellement_mandat_recherche': self.confirmation_paper.avis_renouvellement_mandat_recherche,
            }
            if self.confirmation_paper
            else {}
        )

    def call_webservice(self, data):
        if self.is_doctorate_student:
            DoctorateService.submit_confirmation_paper(
                person=self.person,
                uuid=self.doctorate_uuid,
                **data,
            )
        else:
            DoctorateService.complete_confirmation_paper_by_promoter(
                person=self.person,
                uuid=self.doctorate_uuid,
                **data,
            )
