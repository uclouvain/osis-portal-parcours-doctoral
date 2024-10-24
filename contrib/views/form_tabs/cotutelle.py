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

from parcours_doctoral.contrib.forms.cotutelle import DoctorateCotutelleForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.services.doctorate import DoctorateCotutelleService

__all__ = ['DoctorateCotutelleFormView']


class DoctorateCotutelleFormView(LoadViewMixin, WebServiceFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/cotutelle.html'
    form_class = DoctorateCotutelleForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        return kwargs

    def get_initial(self):
        cotutelle = DoctorateCotutelleService.get_cotutelle(
            person=self.person,
            uuid=self.doctorate_uuid,
        )
        initial = cotutelle.to_dict()
        if initial['cotutelle'] is not None:
            initial['cotutelle'] = 'YES' if initial['cotutelle'] else 'NO'
            if initial['institution_fwb'] is not None:
                initial['institution_fwb'] = 'true' if initial['institution_fwb'] else 'false'
        return initial

    def call_webservice(self, data):
        DoctorateCotutelleService.update_cotutelle(person=self.person, **data)

    def prepare_data(self, data: dict):
        if data['cotutelle'] == 'NO':
            data.update(
                motivation="",
                institution_fwb=None,
                institution="",
                demande_ouverture=[],
                convention=[],
                autres_documents=[],
            )
        del data['cotutelle']
        data['uuid'] = self.doctorate_uuid
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'url' not in context['doctorate'].links['update_cotutelle']:
            raise PermissionDenied(context['doctorate'].links['update_cotutelle']['error'])
        return context
