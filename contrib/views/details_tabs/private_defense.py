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

from django.utils.functional import cached_property
from django.views.generic import TemplateView
from osis_parcours_doctoral_sdk.model.private_defense_dto import PrivateDefenseDTO

from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService

__all__ = [
    'PrivateDefenseDetailView',
]
__namespace__ = False


class PrivateDefenseCommonViewMixin(LoadViewMixin):
    urlpatterns = 'private-defense'

    @cached_property
    def private_defenses(self) -> List[PrivateDefenseDTO]:
        return DoctorateService.get_private_defenses(
            person=self.request.user.person,
            doctorate_uuid=self.doctorate_uuid,
        )

    @cached_property
    def current_private_defense(self) -> PrivateDefenseDTO:
        return next((private_defense for private_defense in self.private_defenses if private_defense.est_active), None)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['all_private_defenses'] = self.private_defenses
        context_data['current_private_defense'] = self.current_private_defense

        supervision_group = DoctorateService.get_supervision(
            person=self.request.user.person,
            uuid_doctorate=self.doctorate_uuid,
        )
        context_data['supervision'] = supervision_group

        return context_data


class PrivateDefenseDetailView(PrivateDefenseCommonViewMixin, TemplateView):
    urlpatterns = 'private-defense'
    template_name = 'parcours_doctoral/details/private_defenses.html'
    permission_link_to_check = 'retrieve_private_defense'
