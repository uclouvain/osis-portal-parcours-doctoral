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
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin

from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.templatetags.parcours_doctoral import can_make_action


class LoadViewMixin(PermissionRequiredMixin, ContextMixin):
    permission_link_to_check = ''

    def has_permission(self):
        if self.doctorate_uuid and self.permission_link_to_check:
            doctorate = self.doctorate

            if not can_make_action(doctorate, self.permission_link_to_check):
                return False

        return True

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.doctorate_uuid:
            context['doctorate'] = self.doctorate

        return context

    @cached_property
    def doctorate_uuid(self):
        return str(self.kwargs.get('pk', ''))

    @cached_property
    def is_doctorate_student(self):
        return self.doctorate.matricule_doctorant == self.request.user.person.global_id

    @cached_property
    def person(self):
        return self.request.user.person

    @cached_property
    def doctorate(self):
        return DoctorateService.get_doctorate(
            person=self.person,
            uuid=self.doctorate_uuid,
        )

    def _get_url(self, tab_name, update=False):
        """Return the URL for the given tab."""
        kwargs = {'pk': self.doctorate_uuid} if self.doctorate_uuid else {}
        with_update = ':update' if update else ''
        return resolve_url(f'parcours_doctoral{with_update}:{tab_name}', **kwargs)
