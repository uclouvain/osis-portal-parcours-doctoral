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

from parcours_doctoral.contrib.forms.private_public_defenses import (
    PrivatePublicDefensesForm,
    PromoterPrivatePublicDefensesForm,
)
from parcours_doctoral.contrib.views.details_tabs.private_defense import (
    PrivateDefenseCommonViewMixin,
)
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = [
    'PrivatePublicDefensesFormView',
]

__namespace__ = False


class PrivatePublicDefensesFormView(PrivateDefenseCommonViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'private-public-defenses'

    @property
    def permission_link_to_check(self):
        return (
            'update_private_public_defenses' if self.is_doctorate_student else 'submit_private_public_defenses_minutes'
        )

    def get_template_names(self):
        return [
            (
                'parcours_doctoral/forms/private_public_defenses.html'
                if self.is_doctorate_student
                else 'parcours_doctoral/forms/private_public_defenses_minutes.html'
            ),
        ]

    def get_form_class(self):
        return PrivatePublicDefensesForm if self.is_doctorate_student else PromoterPrivatePublicDefensesForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.is_doctorate_student:
            form_kwargs['person'] = self.person

        return form_kwargs

    def get_initial(self):
        doctorate = self.doctorate

        initial_data = {
            'titre_these': doctorate.titre_these_propose,
            'langue_soutenance_publique': doctorate.langue_soutenance_publique,
            'date_heure_soutenance_publique': doctorate.date_heure_soutenance_publique,
            'lieu_soutenance_publique': doctorate.lieu_soutenance_publique,
            'local_deliberation': doctorate.local_deliberation,
            'resume_annonce': doctorate.resume_annonce,
            'photo_annonce': doctorate.photo_annonce,
            'proces_verbal_soutenance_publique': doctorate.proces_verbal_soutenance_publique,
        }

        current_private_defense = self.current_private_defense
        if current_private_defense:
            initial_data.update(
                {
                    'date_heure_defense_privee': current_private_defense.date_heure,
                    'lieu_defense_privee': current_private_defense.lieu,
                    'date_envoi_manuscrit': current_private_defense.date_envoi_manuscrit,
                    'proces_verbal_defense_privee': current_private_defense.proces_verbal,
                }
            )

        return initial_data

    def call_webservice(self, data):
        if self.is_doctorate_student:
            DoctorateService.submit_private_public_defenses(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                data=data,
            )
        else:
            DoctorateService.submit_private_public_defenses_minutes(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                data=data,
            )
