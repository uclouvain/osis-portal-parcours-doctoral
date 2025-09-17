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

from parcours_doctoral.contrib.forms.public_defense import PublicDefenseForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = [
    'PublicDefenseFormView',
]


class PublicDefenseFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    @property
    def permission_link_to_check(self):
        return 'update_public_defense' if self.is_doctorate_student else 'update_public_defense'

    def get_template_names(self):
        return [
            (
                'parcours_doctoral/forms/public_defense.html'
                if self.is_doctorate_student
                else 'parcours_doctoral/forms/public_defense.html'
            ),
        ]

    def get_form_class(self):
        return PublicDefenseForm if self.is_doctorate_student else PublicDefenseForm

    def get_initial(self):
        doctorate = self.doctorate
        return {
            'autre_langue': doctorate.autre_langue_soutenance_publique,
            'langue': doctorate.langue_soutenance_publique,
            'date_heure': doctorate.date_heure_soutenance_publique,
            'lieu': doctorate.lieu_soutenance_publique,
            'local_deliberation': doctorate.local_deliberation,
            'resume_annonce': doctorate.resume_annonce,
            'photo_annonce': doctorate.photo_annonce,
        }

    def call_webservice(self, data):
        if self.is_doctorate_student:
            DoctorateService.submit_public_defense(
                person=self.person,
                doctorate_uuid=self.doctorate_uuid,
                data=data,
            )
        else:
            pass
