# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from parcours_doctoral.services.doctorate import DoctorateService
from parcours_doctoral.templatetags.parcours_doctoral import TAB_TREE

__all__ = [
    'DoctorateListView',
    'DoctorateMemberListView',
]
__namespace__ = False


class DoctorateListView(LoginRequiredMixin, TemplateView):
    urlpatterns = {'list': 'list'}
    template_name = 'parcours_doctoral/doctorate_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = DoctorateService().get_doctorates(self.request.user.person)
        context['doctorates'] = result
        context['doctorate_tab_tree'] = TAB_TREE
        return context


class DoctorateMemberListView(LoginRequiredMixin, TemplateView):
    urlpatterns = {'supervised-list': 'supervised'}
    template_name = 'parcours_doctoral/supervised_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctorates'] = DoctorateService().get_supervised_doctorates(self.request.user.person)
        context['tab_tree'] = TAB_TREE
        return context
