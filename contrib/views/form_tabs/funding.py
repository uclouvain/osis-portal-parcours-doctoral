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
from django.views.generic import FormView

from parcours_doctoral.contrib.forms.funding import FundingForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import (
    DoctorateService,
    ParcoursDoctoralBusinessException,
)
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['FundingFormView']


class FundingFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/funding.html'
    permission_link_to_check = 'update_funding'
    error_mapping = {
        ParcoursDoctoralBusinessException.ContratTravailInconsistantException: 'type_contrat_travail',
    }
    form_class = FundingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['admission_type'] = self.doctorate.type_admission
        return kwargs

    def get_initial(self):
        return {
            **self.doctorate.financement.to_dict(),
            'bourse_recherche': self.doctorate.financement.bourse_recherche
            and self.doctorate.financement.bourse_recherche.uuid,
        }

    def call_webservice(self, data):
        DoctorateService.update_funding(
            person=self.person,
            uuid_doctorate=self.doctorate_uuid,
            data=data,
        )
