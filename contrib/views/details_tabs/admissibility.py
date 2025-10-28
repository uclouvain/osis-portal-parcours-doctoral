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
from typing import List

from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic import RedirectView, TemplateView
from osis_document_components.enums import PostProcessingWanted
from osis_parcours_doctoral_sdk.model.admissibility_dto import AdmissibilityDTO

from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService, DoctorateService

__all__ = [
    'AdmissibilityDetailView',
]

__namespace__ = False


class AdmissibilityCommonViewMixin(LoadViewMixin):
    @cached_property
    def admissibilities(self) -> List[AdmissibilityDTO]:
        return DoctorateService.get_admissibilities(
            person=self.request.user.person,
            doctorate_uuid=self.doctorate_uuid,
        )

    @cached_property
    def current_admissibility(self) -> AdmissibilityDTO:
        return next((admissibility for admissibility in self.admissibilities if admissibility.est_active), None)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['all_admissibilities'] = self.admissibilities
        context_data['current_admissibility'] = self.current_admissibility

        jury = DoctorateJuryService.retrieve_jury(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

        context_data['supervisors'] = [member for member in jury.membres if member.est_promoteur]

        return context_data


class AdmissibilityDetailView(AdmissibilityCommonViewMixin, TemplateView):
    urlpatterns = 'admissibility'
    template_name = 'parcours_doctoral/details/admissibility.html'
    permission_link_to_check = 'retrieve_admissibility'
