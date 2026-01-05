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

from parcours_doctoral.contrib.views.details_tabs.private_defense import (
    PrivateDefenseCommonViewMixin,
)

__all__ = [
    'PrivatePublicDefensesDetailView',
]

__namespace__ = False


class PrivatePublicDefensesDetailView(PrivateDefenseCommonViewMixin, TemplateView):
    urlpatterns = 'private-public-defenses'
    template_name = 'parcours_doctoral/details/private_public_defenses.html'
    permission_link_to_check = 'retrieve_private_public_defenses'
