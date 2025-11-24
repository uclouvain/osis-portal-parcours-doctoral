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
from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from parcours_doctoral.contrib.enums import DecisionApprovalEnum
from parcours_doctoral.contrib.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.contrib.views.details_tabs.manuscript_validation import (
    ManuscriptValidationCommonViewMixin,
)
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = [
    'ManuscriptValidationApprovalFormView',
]

__namespace__ = False


class ManuscriptValidationApprovalFormView(ManuscriptValidationCommonViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'manuscript-validation'
    template_name = 'parcours_doctoral/forms/manuscript_validation.html'
    permission_link_to_check = 'validate_manuscript'
    form_class = ManuscriptValidationApprovalForm
    extra_context = {'submit_label': gettext_lazy('Submit my decision')}

    def call_webservice(self, data):
        decision = data.pop('decision', None)

        if decision == DecisionApprovalEnum.DECLINED.name:
            DoctorateService.reject_thesis_by_lead_promoter(
                person=self.person,
                uuid=self.doctorate_uuid,
                data=data,
            )
