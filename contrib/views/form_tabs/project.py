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
from django.core.exceptions import PermissionDenied
from django.views.generic import FormView

from parcours_doctoral.contrib.enums.admission_type import AdmissionType
from parcours_doctoral.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from parcours_doctoral.contrib.enums.financement import ChoixTypeFinancement
from parcours_doctoral.contrib.forms.project import (
    COMMISSIONS_CDE_CLSM,
    COMMISSION_CDSS,
    DoctorateProjectForm,
    SCIENCE_DOCTORATE,
)
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService, PropositionBusinessException
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = ['DoctorateProjectFormView']


class DoctorateProjectFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/project.html'
    proposition = None
    error_mapping = {
        PropositionBusinessException.JustificationRequiseException: 'justification',
        PropositionBusinessException.ProximityCommissionInconsistantException: None,
        PropositionBusinessException.ContratTravailInconsistantException: 'type_contrat_travail',
        PropositionBusinessException.DoctoratNonTrouveException: 'doctorate',
        PropositionBusinessException.InstitutionInconsistanteException: 'institution',
        PropositionBusinessException.DomaineTheseInconsistantException: 'domaine_these',
    }
    form_class = DoctorateProjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        return kwargs

    def get_initial(self):
        if 'url' not in self.doctorate.links['update_project']:
            raise PermissionDenied(self.doctorate.links['update_project']['error'])
        return {
            **self.doctorate.to_dict(),
            'sector': self.doctorate.code_secteur_formation,
            'doctorate': "{sigle}-{annee}".format(
                sigle=self.doctorate.doctorat.sigle,
                annee=self.doctorate.doctorat.annee,
            ),
            'bourse_recherche': self.doctorate.bourse_recherche and self.doctorate.bourse_recherche.uuid,
        }

    def prepare_data(self, data):
        # Process the form data to match API
        if self.doctorate.type_admission != AdmissionType.PRE_ADMISSION.name:
            data['justification'] = ''

        if data['type_financement'] != ChoixTypeFinancement.WORK_CONTRACT.name:
            data['type_contrat_travail'] = ''
            data['eft'] = None

        if data['type_financement'] != ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            data['bourse_recherche'] = ''
            data['autre_bourse_recherche'] = ''

        if not data['type_financement']:
            data['duree_prevue'] = None
            data['temps_consacre'] = None

        if data['doctorat_deja_realise'] not in [
            ChoixDoctoratDejaRealise.YES.name,
            ChoixDoctoratDejaRealise.PARTIAL.name,
        ]:
            data['institution'] = ''
            data['domaine_these'] = ''
            data['non_soutenue'] = None
            data['date_soutenance'] = None
            data['raison_non_soutenue'] = ''

        if data['non_soutenue']:
            data['date_soutenance'] = None
        else:
            data['raison_non_soutenue'] = ''

        # TODO to delete api side ?
        data['commission_proximite'] = self.doctorate.commission_proximite

        return data

    def call_webservice(self, data):
        data['uuid'] = self.doctorate_uuid
        DoctorateService.update_proposition(person=self.person, **data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['COMMISSIONS_CDE_CLSM'] = COMMISSIONS_CDE_CLSM
        context['COMMISSION_CDSS'] = COMMISSION_CDSS
        context['SCIENCE_DOCTORATE'] = SCIENCE_DOCTORATE
        return context
