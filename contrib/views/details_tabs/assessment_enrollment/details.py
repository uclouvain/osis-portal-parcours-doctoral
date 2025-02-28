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

from django.views.generic import TemplateView

from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.training import DoctorateTrainingService

__namespace__ = False

__all__ = [
    'AssessmentEnrollmentDetailsView',
]


class AssessmentEnrollmentDetailsView(LoadViewMixin, TemplateView):
    urlpatterns = 'details'
    template_name = 'parcours_doctoral/details/training/assessment_enrollment.html'
    permission_link_to_check = 'retrieve_assessment_enrollment'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['assessment_enrollment'] = DoctorateTrainingService.retrieve_assessment_enrollment(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
            enrollment_uuid=str(self.kwargs['enrollment_uuid']),
        )

        return context_data
