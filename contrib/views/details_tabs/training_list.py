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

from copy import copy

from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import FormView

from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException
from parcours_doctoral.contrib.enums import CategorieActivite, StatutActivite
from parcours_doctoral.contrib.forms.training import BatchActivityForm
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.services.training import DoctorateTrainingService

__all__ = [
    'DoctoralTrainingListView',
    'ComplementaryTrainingListView',
    'CourseEnrollmentListView',
]
__namespace__ = False


class DoctoralTrainingListView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'doctoral-training'
    template_name = 'parcours_doctoral/training_list.html'
    form_class = BatchActivityForm
    permission_link_to_check = 'retrieve_doctorate_training'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['activities'] = self.activities
        context_data['statuses'] = StatutActivite.choices()
        config = DoctorateTrainingService.get_config(person=self.person, uuid=self.doctorate_uuid)
        original_constants = list(dict(CategorieActivite.choices()).keys())
        original_constants.remove(CategorieActivite.UCL_COURSE.name)
        context_data['categories'] = list(zip(original_constants, config.category_labels[get_language()]))
        context_data['activities_form'] = context_data.pop('form')  # Trick template
        return context_data

    @cached_property
    def activities(self):
        return DoctorateTrainingService.list_doctoral_training(
            person=self.person,
            uuid=self.doctorate_uuid,
        )

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or self.request.get_full_path()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['uuids'] = [activity.uuid for activity in self.activities]
        return kwargs

    def prepare_data(self, data):
        return {'activity_uuids': data['activity_ids']}

    def call_webservice(self, data):
        return DoctorateTrainingService.submit_activities(self.person, self.doctorate_uuid, **data)

    def form_valid(self, form):
        data = self.prepare_data(copy(form.cleaned_data))

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:
            form.activities_in_error = []
            for exception in multiple_business_api_exception.exceptions:
                form.add_error(None, exception.detail)
                form.activities_in_error.append(exception.activite_id)
            return self.form_invalid(form)
        return super(WebServiceFormMixin, self).form_valid(form)


class ComplementaryTrainingListView(DoctoralTrainingListView):
    urlpatterns = 'complementary-training'
    template_name = "parcours_doctoral/complementary_training_list.html"
    permission_link_to_check = 'retrieve_complementary_training'

    @cached_property
    def activities(self):
        return DoctorateTrainingService.list_complementary_training(
            person=self.person,
            uuid=self.doctorate_uuid,
        )


class CourseEnrollmentListView(DoctoralTrainingListView):
    urlpatterns = 'course-enrollment'
    template_name = "parcours_doctoral/course_enrollment.html"
    permission_link_to_check = 'retrieve_course_enrollment'

    @cached_property
    def activities(self):
        return DoctorateTrainingService.list_course_enrollment(
            person=self.person,
            uuid=self.doctorate_uuid,
        )
