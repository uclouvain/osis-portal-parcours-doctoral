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

from django.views.generic import FormView

from parcours_doctoral.contrib.forms.private_defense import PrivateDefenseForm
from parcours_doctoral.contrib.views.details_tabs.private_defense import (
    PrivateDefenseCommonViewMixin,
)
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['PrivateDefenseFormView']


class PrivateDefenseFormView(PrivateDefenseCommonViewMixin, WebServiceFormMixin, FormView):
    permission_link_to_check = 'update_private_defense'
    template_name = 'parcours_doctoral/forms/private_defenses.html'
    form_class = PrivateDefenseForm

    def get_initial(self):
        current_private_defense = self.current_private_defense
        return (
            {
                'titre_these': current_private_defense.titre_these,
                'date_heure': current_private_defense.date_heure,
                'lieu': current_private_defense.lieu,
                'date_envoi_manuscrit': current_private_defense.date_envoi_manuscrit,
                'proces_verbal': current_private_defense.proces_verbal,
            }
            if current_private_defense
            else {}
        )

    def call_webservice(self, data):
        DoctorateService.submit_private_defense(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            private_defense_uuid=self.current_private_defense.uuid,
            data=data,
        )
