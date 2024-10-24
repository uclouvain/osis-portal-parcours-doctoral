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
from django.shortcuts import redirect
from django.views.generic import FormView

from parcours_doctoral.contrib.enums.actor import ActorType
from parcours_doctoral.contrib.forms.supervision import ACTOR_EXTERNAL, DoctorateSupervisionForm, EXTERNAL_FIELDS
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateSupervisionService, DoctorateService
from parcours_doctoral.services.mixins import WebServiceFormMixin


class SupervisionFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/supervision.html'
    form_class = DoctorateSupervisionForm
    extra_context = {'custom_form_template': True}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supervision'] = DoctorateService.get_supervision(
            person=self.request.user.person,
            uuid_doctorate=self.doctorate_uuid,
        )
        context['signature_conditions'] = DoctorateSupervisionService.get_signature_conditions(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )
        context['add_form'] = context.pop('form')  # Trick template to not add button
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'url' not in context['doctorate'].links['request_signatures']:
            return redirect('parcours_doctoral:supervision', **self.kwargs)
        return self.render_to_response(context)

    def prepare_data(self, data):
        is_external = data.pop('internal_external') == ACTOR_EXTERNAL
        promoter = data.pop('tutor')
        ca_member = data.pop('person')
        matricule = (ca_member if data['type'] == ActorType.CA_MEMBER.name else promoter) if not is_external else ""
        if not is_external:
            # Remove data about external actor
            data = {**data, **{f: '' for f in EXTERNAL_FIELDS}}
        return {
            'type': data['type'],
            'matricule': matricule,
            **data,
        }

    def call_webservice(self, data):
        return DoctorateSupervisionService.add_member(person=self.person, uuid=self.doctorate_uuid, **data)
