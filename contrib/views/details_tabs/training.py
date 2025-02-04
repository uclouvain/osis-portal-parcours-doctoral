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

from abc import ABC
from typing import Tuple, Union

from django.forms import Form
from django.http import Http404
from django.shortcuts import resolve_url
from django.template import Context, Template
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import FormView
from django.views.generic.edit import FormMixin

from parcours_doctoral.contrib.enums.training import (
    CategorieActivite,
    ContexteFormation,
)
from parcours_doctoral.contrib.forms.training import *
from parcours_doctoral.contrib.views.mixins import LoadViewMixin
from parcours_doctoral.services.mixins import WebServiceFormMixin
from parcours_doctoral.services.training import DoctorateTrainingService

__all__ = [
    "TrainingActivityAddView",
    "TrainingActivityEditView",
    "TrainingActivityDeleteView",
    "TrainingActivityAssentView",
]
__namespace__ = {
    'doctoral-training': 'doctoral-training',
    'complementary-training': 'complementary-training',
    'course-enrollment': 'course-enrollment',
}


class TrainingActivityFormMixin(LoadViewMixin, WebServiceFormMixin, FormMixin, ABC):
    template_name = "parcours_doctoral/forms/training.html"
    form_class_mapping = {
        "doctoral-training": {
            CategorieActivite.CONFERENCE: ConferenceForm,
            (CategorieActivite.CONFERENCE, CategorieActivite.COMMUNICATION): ConferenceCommunicationForm,
            (CategorieActivite.CONFERENCE, CategorieActivite.PUBLICATION): ConferencePublicationForm,
            CategorieActivite.RESIDENCY: ResidencyForm,
            (CategorieActivite.RESIDENCY, CategorieActivite.COMMUNICATION): ResidencyCommunicationForm,
            CategorieActivite.COMMUNICATION: CommunicationForm,
            CategorieActivite.PUBLICATION: PublicationForm,
            CategorieActivite.SERVICE: ServiceForm,
            CategorieActivite.SEMINAR: SeminarForm,
            (CategorieActivite.SEMINAR, CategorieActivite.COMMUNICATION): SeminarCommunicationForm,
            CategorieActivite.VAE: ValorisationForm,
            CategorieActivite.COURSE: CourseForm,
        },
        "complementary-training": {
            CategorieActivite.COURSE: ComplementaryCourseForm,
        },
        "course-enrollment": {
            CategorieActivite.UCL_COURSE: UclCourseForm,
        },
    }
    activity_uuid = None

    @property
    def namespace(self) -> str:
        """Return current url namespace, i.e.: doctoral-training, complementary-training or course-enrollment"""
        return self.request.resolver_match.namespaces[1]

    @property
    def category(self) -> str:
        """Return category being worked on"""
        return str(getattr(self, 'activity', self.kwargs).get('category')).upper()

    def get_form_class(self):
        try:
            return self.form_class_mapping[self.namespace][self.category_mapping_key]
        except KeyError as e:
            raise Http404(f"No form mapped: {e}")

    @cached_property
    def category_mapping_key(self) -> Union[Tuple[CategorieActivite, CategorieActivite], CategorieActivite]:
        """Return the form_class mapping key (with parent if needed)"""
        category = CategorieActivite[self.category]
        parent_id = getattr(self, 'activity', self.request.GET).get('parent')
        if parent_id:
            parent = DoctorateTrainingService.retrieve_activity(
                person=self.request.user.person,
                doctorate_uuid=self.doctorate_uuid,
                activity_uuid=parent_id,
            )
            return CategorieActivite[str(parent.category)], category
        return category

    @cached_property
    def config(self):
        return DoctorateTrainingService.get_config(person=self.person, uuid=self.doctorate_uuid)

    def get_success_url(self):
        base_url = resolve_url(':'.join(self.request.resolver_match.namespaces), pk=self.kwargs['pk'])
        return self.request.POST.get('redirect_to') or f"{base_url}#{self.activity_uuid}"

    def prepare_data(self, data):
        data = super().prepare_data(data)
        data['object_type'] = self.get_form_class().object_type

        # Get category from edited object or view kwargs
        from osis_parcours_doctoral_sdk.model.categorie_activite import (
            CategorieActivite,
        )
        from osis_parcours_doctoral_sdk.model.contexte_formation import (
            ContexteFormation as ContexteFormationModel,
        )

        data['category'] = CategorieActivite(self.category)

        if 'context' not in data:
            # When on a non-UCLCourseForm, context is not passed, give it current context
            data['context'] = ContexteFormationModel(
                ContexteFormation.COMPLEMENTARY_TRAINING.name
                if self.namespace == "complementary-training"
                else ContexteFormation.DOCTORAL_TRAINING.name
            )
        else:
            # When on an UCLCourseForm, context is passed, convert context
            data['context'] = ContexteFormationModel(data['context'])

        # Data cleanup and coercion
        if 'parent' not in data:
            data['parent'] = self.request.GET.get('parent')
        for decimal_field in ['ects', 'participating_days']:
            if decimal_field in data:
                if not data[decimal_field]:
                    data[decimal_field] = 0.0
                else:
                    data[decimal_field] = float(data[decimal_field])
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['config_types'] = self.config
        kwargs['person'] = self.person
        kwargs['doctorate'] = self.doctorate
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        original_constants = dict(CategorieActivite.choices()).keys()
        context_data['categories'] = dict(zip(original_constants, self.config.category_labels[get_language()]))
        return context_data


class TrainingActivityAddView(TrainingActivityFormMixin, FormView):
    urlpatterns = {'add': 'add/<str:category>'}

    def call_webservice(self, data):
        response = DoctorateTrainingService.create_activity(
            person=self.person,
            uuid=self.doctorate_uuid,
            **data,
        )
        self.activity_uuid = response['uuid']


class TrainingActivityEditView(TrainingActivityFormMixin, FormView):
    urlpatterns = {'edit': 'edit/<uuid:activity_id>'}
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'

    def get_initial(self):
        return self.activity

    @cached_property
    def activity(self):
        return DoctorateTrainingService.retrieve_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def prepare_data(self, data):
        data['category'] = self.activity['category']
        data['parent'] = self.activity.get('parent')
        return super().prepare_data(data)

    def call_webservice(self, data):
        response = DoctorateTrainingService.update_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
            **data,
        )
        self.activity_uuid = response['uuid']


class TrainingActivityDeleteView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'delete': 'delete/<uuid:activity_id>'}
    template_name = "parcours_doctoral/forms/training/activity_confirm_delete.html"
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'
    form_class = Form

    def call_webservice(self, data):
        DoctorateTrainingService.delete_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
        )

    @cached_property
    def activity(self):
        return DoctorateTrainingService.retrieve_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def get_context_data(self, **kwargs):
        kwargs['object'] = (
            Template(
                """{% load parcours_doctoral %}
            {% firstof 0 activity.category|lower|add:'.html' as template_name %}
            {% include "parcours_doctoral/details/training/_activity_title.html" %}
            """
            )
            .render(Context({'activity': self.activity, 'request': self.request}))
            .strip()
        )
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or resolve_url(
            ':'.join(self.request.resolver_match.namespaces),
            pk=self.kwargs['pk'],
        )


class TrainingActivityAssentView(LoadViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'assent': 'assent/<uuid:activity_id>'}
    template_name = "parcours_doctoral/forms/training/assent.html"
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'
    form_class = AssentForm

    def call_webservice(self, data):
        DoctorateTrainingService.assent_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
            **data,
        )

    def get_initial(self):
        assent = self.activity['reference_promoter_assent']
        return {
            'approbation': True if assent is None else assent,
            'commentaire': self.activity['reference_promoter_comment'],
        }

    def get_context_data(self, **kwargs):
        kwargs['activity'] = self.activity
        kwargs['object'] = (
            Template(
                """{% load parcours_doctoral %}
            {% firstof 0 activity.category|lower|add:'.html' as template_name %}
            {% include "parcours_doctoral/details/training/_activity_title.html" %}
            """
            )
            .render(Context({'activity': self.activity, 'request': self.request}))
            .strip()
        )
        return super().get_context_data(**kwargs)

    @cached_property
    def activity(self):
        return DoctorateTrainingService.retrieve_activity(
            person=self.person,
            doctorate_uuid=self.doctorate_uuid,
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or resolve_url(
            ':'.join(self.request.resolver_match.namespaces),
            pk=self.kwargs['pk'],
        )
