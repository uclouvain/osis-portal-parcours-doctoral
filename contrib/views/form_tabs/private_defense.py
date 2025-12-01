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

from parcours_doctoral.contrib.forms.private_defense import (
    PrivateDefenseForm,
    PromoterPrivateDefenseForm,
)
from parcours_doctoral.contrib.views.details_tabs.private_defense import (
    PrivateDefenseCommonViewMixin,
)
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['PrivateDefenseFormView']


class PrivateDefenseFormView(PrivateDefenseCommonViewMixin, WebServiceFormMixin, FormView):
    @property
    def permission_link_to_check(self):
        return 'update_private_defense' if self.is_doctorate_student else 'submit_private_defense_minutes'

    def get_template_names(self):
        return [
            (
                'parcours_doctoral/forms/private_defenses.html'
                if self.is_doctorate_student
                else 'parcours_doctoral/forms/private_defenses_minutes.html'
            ),
        ]

    def get_form_class(self):
        return PrivateDefenseForm if self.is_doctorate_student else PromoterPrivateDefenseForm

    def get_initial(self):
        initial_data = {
            'titre_these': self.doctorate.titre_these_propose,
        }

        current_private_defense = self.current_private_defense

        if current_private_defense:
            initial_data['date_heure_defense_privee'] = current_private_defense.date_heure
            initial_data['lieu_defense_privee'] = current_private_defense.lieu
            initial_data['date_envoi_manuscrit'] = current_private_defense.date_envoi_manuscrit
            initial_data['proces_verbal_defense_privee'] = current_private_defense.proces_verbal

        return initial_data

    def call_webservice(self, data):
        if self.is_doctorate_student:
            DoctorateService.submit_private_defense(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                data={
                    'titre_these': data['titre_these'],
                    'date_heure': data['date_heure_defense_privee'],
                    'lieu': data['lieu_defense_privee'],
                    'date_envoi_manuscrit': data['date_envoi_manuscrit'],
                },
            )
        else:
            DoctorateService.submit_private_defense_minutes(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                private_defense_uuid=self.current_private_defense.uuid,
                data={
                    'proces_verbal': data['proces_verbal_defense_privee'],
                },
            )
