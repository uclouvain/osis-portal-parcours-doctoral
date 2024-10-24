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

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.services.doctorate import DoctorateService

__all__ = ['DoctorateRequestSignaturesView']


class DoctorateRequestSignaturesView(LoginRequiredMixin, SuccessMessageMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'request-signatures'
    form_class = Form
    success_message = _("Signature requests sent")

    def call_webservice(self, data):
        DoctorateService.request_signatures(person=self.person, uuid=str(self.kwargs.get('pk')))

    def form_invalid(self, form):
        messages.error(self.request, _("Please first correct the erros"))
        return HttpResponseRedirect(resolve_url("parcours_doctoral:update:supervision", pk=self.kwargs.get('pk')))

    def get_success_url(self):
        return resolve_url("parcours_doctoral:supervision", pk=self.kwargs.get('pk'))
