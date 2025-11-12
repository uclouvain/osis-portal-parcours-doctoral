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
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.views.generic import FormView

from parcours_doctoral.contrib.forms.authorization_distribution import (
    AuthorizationDistributionForm,
)
from parcours_doctoral.contrib.views.details_tabs.authorization_distribution import (
    AuthorizationDistributionCommonViewMixin,
)
from parcours_doctoral.services.doctorate import (
    AuthorizationDistributionBusinessException,
    DoctorateService,
)
from parcours_doctoral.services.mixins import WebServiceFormMixin

__all__ = [
    'AuthorizationDistributionFormView',
]

__namespace__ = False


class AuthorizationDistributionFormView(AuthorizationDistributionCommonViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'authorization-distribution'
    template_name = 'parcours_doctoral/forms/authorization_distribution.html'
    permission_link_to_check = 'update_authorization_distribution'
    form_class = AuthorizationDistributionForm
    error_mapping = {
        AuthorizationDistributionBusinessException.SourcesFinancementsNonCompleteesException: 'sources_financement',
        AuthorizationDistributionBusinessException.ResumeAnglaisNonCompleteException: 'resume_anglais',
        AuthorizationDistributionBusinessException.LangueRedactionTheseNonCompleteeException: 'langue_redaction_these',
        AuthorizationDistributionBusinessException.MotsClesNonCompletesException: 'mots_cles',
        AuthorizationDistributionBusinessException.TypeModalitesDiffusionNonCompleteException: (
            'type_modalites_diffusion'
        ),
        AuthorizationDistributionBusinessException.DateEmbargoModalitesDiffusionNonCompleteeException: 'date_embargo',
        AuthorizationDistributionBusinessException.ModalitesDiffusionNonAccepteesException: 'accepter_conditions',
    }

    @cached_property
    def accepted_text(self):
        return render_to_string(
            'parcours_doctoral/includes/authorization_distribution/authorization_distribution_acceptation.html'
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['accepted_text'] = self.accepted_text
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['person'] = self.person
        return form_kwargs

    def get_initial(self):
        authorization_distribution = self.authorization_distribution

        initial_data = (
            {
                'sources_financement': authorization_distribution.sources_financement,
                'resume_anglais': authorization_distribution.resume_anglais,
                'resume_autre_langue': authorization_distribution.resume_autre_langue,
                'mots_cles': authorization_distribution.mots_cles,
                'type_modalites_diffusion': authorization_distribution.type_modalites_diffusion,
                'date_embargo': authorization_distribution.date_embargo,
                'limitations_additionnelles_chapitres': authorization_distribution.limitations_additionnelles_chapitres,
                'accepter_conditions': bool(authorization_distribution.modalites_diffusion_acceptees_le),
            }
            if authorization_distribution
            else {}
        )

        initial_data['langue_redaction_these'] = self.doctorate.projet.langue_redaction_these

        return initial_data

    def call_webservice(self, data):
        data['modalites_diffusion_acceptees'] = self.accepted_text if data.pop('accepter_conditions', None) else ''
        DoctorateService.update_authorization_distribution(
            person=self.person,
            uuid=self.doctorate_uuid,
            data=data,
        )
