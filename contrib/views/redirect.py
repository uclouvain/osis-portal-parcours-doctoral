# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import RedirectView

from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.templatetags.parcours_doctoral import can_make_action

__all__ = ['DoctorateRedirectView']

__namespace__ = False


class DoctorateRedirectView(LoadViewMixin, RedirectView):
    urlpatterns = {
        'base': '<uuid:pk>/',
    }

    def get_redirect_url(self, *args, **kwargs):
        """
        Override get_redirect_url to not include kwargs for the listing view.
        """
        try:
            doctorate = self.doctorate

            if can_make_action(doctorate, 'retrieve_project'):
                self.pattern_name = 'parcours_doctoral:project'
                return super().get_redirect_url(*args, **kwargs)

        except PermissionDenied:
            pass

        return reverse('parcours_doctoral:list')
