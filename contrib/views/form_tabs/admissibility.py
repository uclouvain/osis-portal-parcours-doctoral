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

from parcours_doctoral.contrib.forms.admissibility import AdmissibilityForm
from parcours_doctoral.contrib.views.details_tabs.admissibility import (
    AdmissibilityCommonViewMixin,
)
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['AdmissibilityFormView']


class AdmissibilityFormView(AdmissibilityCommonViewMixin, WebServiceFormMixin, FormView):
    @property
    def permission_link_to_check(self):
        return 'update_admissibility' if self.is_doctorate_student else 'update_admissibility'

    def get_template_names(self):
        return [
            (
                'parcours_doctoral/forms/admissibility.html'
                if self.is_doctorate_student
                else 'parcours_doctoral/forms/admissibility.html'
            ),
        ]

    def get_form_class(self):
        return AdmissibilityForm if self.is_doctorate_student else AdmissibilityForm

    def get_initial(self):
        initial_data = {
            'titre_these': self.doctorate.titre_these_propose,
        }

        current_admissibility = self.current_admissibility
        if current_admissibility:
            initial_data['date_decision'] = current_admissibility.date_decision
            initial_data['date_envoi_manuscrit'] = current_admissibility.date_envoi_manuscrit
            initial_data['proces_verbal'] = current_admissibility.proces_verbal
            initial_data['avis_jury'] = current_admissibility.avis_jury

        return initial_data

    def call_webservice(self, data):
        if self.is_doctorate_student:
            DoctorateService.submit_admissibility(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                data=data,
            )
