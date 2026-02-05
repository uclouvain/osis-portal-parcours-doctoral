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
from osis_parcours_doctoral_sdk.models.authorization_distribution_dto import (
    AuthorizationDistributionDTO,
)
from osis_parcours_doctoral_sdk.models.private_defense_dto import PrivateDefenseDTO

from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService, DoctorateService

__all__ = [
    'AuthorizationDistributionDetailView',
]

__namespace__ = False


class AuthorizationDistributionCommonViewMixin(LoadViewMixin):
    @cached_property
    def authorization_distribution(self) -> AuthorizationDistributionDTO:
        return DoctorateService.get_authorization_distribution(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['authorization_distribution'] = self.authorization_distribution
        return context_data

    def get_success_url(self):
        return resolve_url('parcours_doctoral:authorization-distribution', pk=self.doctorate_uuid)


class AuthorizationDistributionDetailView(AuthorizationDistributionCommonViewMixin, TemplateView):
    urlpatterns = 'authorization-distribution'
    template_name = 'parcours_doctoral/details/authorization_distribution.html'
    permission_link_to_check = 'retrieve_authorization_distribution'
