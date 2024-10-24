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
from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from parcours_doctoral.contrib.forms.jury.membre import JuryMembreForm
from parcours_doctoral.contrib.forms.jury.preparation import JuryPreparationForm
from parcours_doctoral.contrib.views.details_tabs.jury import LoadJuryViewMixin, JuryDetailView
from parcours_doctoral.services.doctorate import DoctorateJuryService, JuryBusinessException
from parcours_doctoral.services.mixins import WebServiceFormMixin

__namespace__ = False

__all__ = [
    'JuryPreparationFormView',
    'JuryFormView',
]


class JuryPreparationFormView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/forms/jury/preparation.html'
    form_class = JuryPreparationForm
    permission_link_to_check = 'update_jury_preparation'

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


class JuryFormView(JuryDetailView, WebServiceFormMixin, FormView):
    form_class = JuryMembreForm
    error_mapping = {
        JuryBusinessException.NonDocteurSansJustificationException: "justification_non_docteur",
        JuryBusinessException.MembreExterneSansInstitutionException: "institution",
        JuryBusinessException.MembreExterneSansPaysException: "pays",
        JuryBusinessException.MembreExterneSansNomException: "nom",
        JuryBusinessException.MembreExterneSansPrenomException: "prenom",
        JuryBusinessException.MembreExterneSansTitreException: "titre",
        JuryBusinessException.MembreExterneSansGenreException: "genre",
        JuryBusinessException.MembreExterneSansEmailException: "email",
        JuryBusinessException.MembreDejaDansJuryException: "matricule",
    }
    extra_context = {'submit_label': gettext_lazy('Add')}
    permission_link_to_check = 'create_jury_members'

    def call_webservice(self, data):
        return DoctorateJuryService.create_jury_member(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )

    @property
    def success_url(self):
        return self.request.path
