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

from django.utils.functional import cached_property
from django.views.generic import TemplateView

from parcours_doctoral.contrib.enums import RoleJury
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService

__namespace__ = False

__all__ = [
    'JuryPreparationDetailView',
    'JuryDetailView',
]


class LoadJuryViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    @cached_property
    def jury(self):
        return DoctorateJuryService.retrieve_jury(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        return context


class JuryPreparationDetailView(LoadJuryViewMixin, TemplateView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/details/jury/preparation.html'
    permission_link_to_check = 'retrieve_jury_preparation'


class JuryDetailView(LoadJuryViewMixin, TemplateView):
    urlpatterns = 'jury'
    template_name = 'parcours_doctoral/forms/jury/jury.html'
    permission_link_to_check = 'list_jury_members'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        membres = DoctorateJuryService.list_jury_members(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )
        context_data['membres'] = (membre for membre in membres if membre.role == RoleJury.MEMBRE.name)
        context_data['membre_president'] = (membre for membre in membres if membre.role == RoleJury.PRESIDENT.name)
        context_data['membre_secretaire'] = (membre for membre in membres if membre.role == RoleJury.SECRETAIRE.name)
        return context_data
