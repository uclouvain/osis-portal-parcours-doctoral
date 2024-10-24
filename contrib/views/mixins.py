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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin

from parcours_doctoral.services.doctorate import DoctorateService


class LoadViewMixin(LoginRequiredMixin, ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.doctorate_uuid:
            context['doctorate'] = self.doctorate

        return context

    @cached_property
    def doctorate_uuid(self):
        return str(self.kwargs.get('pk', ''))

    @cached_property
    def person(self):
        return self.request.user.person

    @cached_property
    def doctorate(self):
        # Simulate the merging of the doctorate and the proposition TODO to remove after the refactoring
        proposition = DoctorateService.get_proposition(
            person=self.person,
            uuid=self.doctorate_uuid,
        )
        doctorat = DoctorateService.get_doctorate(
            person=self.person,
            uuid=self.doctorate_uuid,
        )
        for field in [
            'titre_these',
            'matricule_doctorant',
            'noma_doctorant',
            'genre_doctorant',
            'prenom_doctorant',
            'nom_doctorant',
            'statut',
        ]:
            setattr(proposition, field, getattr(doctorat, field))
        for link_key, link_value in doctorat.links.to_dict().items():
            proposition.links.set_attribute(link_key, link_value)
        return proposition

    def _get_url(self, tab_name, update=False):
        """Return the URL for the given tab."""
        kwargs = {'pk': self.doctorate_uuid} if self.doctorate_uuid else {}
        with_update = ':update' if update else ''
        return resolve_url(f'parcours_doctoral{with_update}:{tab_name}', **kwargs)
