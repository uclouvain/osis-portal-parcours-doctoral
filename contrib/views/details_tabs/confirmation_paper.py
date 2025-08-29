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

from django.views.generic import TemplateView, RedirectView
from osis_document.enums import PostProcessingWanted

from osis_document_components.utils import get_file_url
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.doctorate import DoctorateService

__all__ = [
    'ConfirmationPaperDetailView',
    'ConfirmationPaperCanvasExportView',
]
__namespace__ = False


class ConfirmationPaperDetailView(LoadViewMixin, TemplateView):
    urlpatterns = {'confirmation-paper': 'confirmation'}
    template_name = 'parcours_doctoral/details/confirmation_papers.html'
    permission_link_to_check = 'retrieve_confirmation'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        all_confirmation_papers = DoctorateService.get_confirmation_papers(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        )

        if all_confirmation_papers:
            context_data['current_confirmation_paper'] = all_confirmation_papers.pop(0)

        context_data['previous_confirmation_papers'] = all_confirmation_papers

        return context_data


class ConfirmationPaperCanvasExportView(LoadViewMixin, RedirectView):
    urlpatterns = 'confirmation-paper-canvas'
    permission_link_to_check = 'retrieve_confirmation'

    def get(self, request, *args, **kwargs):
        from osis_document_components.services import get_remote_token

        canvas_uuid = DoctorateService.get_last_confirmation_paper_canvas(
            person=self.request.user.person,
            uuid=self.doctorate_uuid,
        ).uuid

        reading_token = get_remote_token(
            canvas_uuid,
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
        )

        self.url = get_file_url(reading_token)

        return super().get(request, *args, **kwargs)
