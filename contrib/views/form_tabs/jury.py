# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import PermissionDenied
from django.views.generic import FormView

from parcours_doctoral.contrib.forms.jury.preparation import JuryPreparationForm
from parcours_doctoral.contrib.views.details_tabs.jury import LoadJuryViewMixin
from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.services.doctorate import DoctorateJuryService


__all__ = [
    'DoctorateJuryFormView',
]
__namespace__ = False


class DoctorateJuryFormView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/forms/jury/preparation.html'
    form_class = JuryPreparationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        return kwargs

    def get_initial(self):
        return {
            'titre_propose': self.jury.titre_propose,
            'formule_defense': self.jury.formule_defense,
            'date_indicative': self.jury.date_indicative,
            'langue_redaction': self.jury.langue_redaction,
            'langue_soutenance': self.jury.langue_soutenance,
            'commentaire': self.jury.commentaire,
        }

    def call_webservice(self, data):
        return DoctorateJuryService.modifier_jury(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'url' not in context['doctorate'].links['update_jury_preparation']:
            raise PermissionDenied(context['doctorate'].links['update_jury_preparation']['error'])
        return context
