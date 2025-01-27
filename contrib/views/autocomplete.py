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
import itertools
from typing import List

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_organisation_sdk.model.entite_type_enum import EntiteTypeEnum
from osis_reference_sdk.model.scholarship import Scholarship
from osis_reference_sdk.model.university import University

from base.models.enums.entity_type import INSTITUTE
from parcours_doctoral.constants import BE_ISO_CODE
from parcours_doctoral.contrib.enums.diploma import StudyType
from parcours_doctoral.services.autocomplete import DoctorateAutocompleteService
from parcours_doctoral.services.organisation import EntitiesService
from parcours_doctoral.services.reference import (
    CountriesService,
    LanguageService,
    SuperiorNonUniversityService,
    UniversityService,
)
from parcours_doctoral.utils import (
    format_entity_title,
    format_scholarship,
    format_school_title,
)

__all__ = [
    "CountryAutocomplete",
    "LanguageAutocomplete",
    "TutorAutocomplete",
    "PersonAutocomplete",
    "InstituteAutocomplete",
    "LearningUnitYearsAutocomplete",
    "ScholarshipAutocomplete",
    "SuperiorInstituteAutocomplete",
]

LANGUAGE_FR = 'FR'
LANGUAGE_EN = 'EN'
LANGUAGE_UNDECIDED = 'XX'

TRUTHY_VALUES = [True, "True", "true"]


class PaginatedAutocompleteMixin:
    paginate_by = 20
    page_kwargs = 'page'

    def get_page(self):
        try:
            return int(self.request.GET.get(self.page_kwargs, 1))
        except Exception:
            return 1

    def get_webservice_pagination_kwargs(self):
        return {
            'limit': self.paginate_by,
            'offset': (self.get_page() - 1) * self.paginate_by,
        }

    def get_list(self):
        raise NotImplementedError

    def results(self, results):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        """Return option list json response."""
        results = self.get_list()
        return JsonResponse(
            {'results': self.results(results), 'pagination': {'more': len(results) >= self.paginate_by}}
        )


class ScholarshipAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'scholarship'

    def get_list(self):
        # TODO to replace by the reference service
        return DoctorateAutocompleteService.get_scholarships(
            person=self.request.user.person,
            search=self.q,
            **self.get_webservice_pagination_kwargs(),
        ).get('results')

    def results(self, results: List[Scholarship]):
        return [
            dict(
                id="{result.uuid}".format(result=result),
                text=format_scholarship(result),
            )
            for result in results
        ]


class CountryAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'country'

    def get_list(self):
        return CountriesService.get_countries(
            person=self.request.user.person,
            search=self.q,
            **self.get_webservice_pagination_kwargs(),
        )

    def results(self, results):
        page = self.get_page()
        belgique = []
        if not self.q and not self.forwarded.get('exclude_be', False) and page == 1:
            belgique = [
                {
                    'id': BE_ISO_CODE,
                    'text': _('Belgium'),
                    'european_union': True,
                },
                {'id': None, 'text': '<hr>'},
            ]
        return belgique + [
            dict(
                id=country.iso_code,
                text=country.name if get_language() == settings.LANGUAGE_CODE else country.name_en,
                european_union=country.european_union,
            )
            for country in results
            if not self.forwarded.get('exclude_be', False) or country.iso_code != BE_ISO_CODE
        ]


class LanguageAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'language'

    def get_list(self):
        return LanguageService.get_languages(
            person=self.request.user.person,
            search=self.q,
            **self.get_webservice_pagination_kwargs(),
        )

    def results(self, results):
        page = self.get_page()

        top_languages = []
        top_languages_codes = {LANGUAGE_FR, LANGUAGE_EN, LANGUAGE_UNDECIDED}
        show_top_languages = not self.q and page == 1 and self.forwarded.get('show_top_languages', False)
        if show_top_languages:
            top_languages = [
                {
                    'id': LANGUAGE_FR,
                    'text': _('French'),
                },
                {
                    'id': LANGUAGE_EN,
                    'text': _('English'),
                },
                {
                    'id': LANGUAGE_UNDECIDED,
                    'text': _('Undecided'),
                },
                {'id': None, 'text': '<hr>'},
            ]
        return top_languages + [
            dict(
                id=language.code,
                text=language.name if get_language() == settings.LANGUAGE_CODE else language.name_en,
            )
            for language in results
            if not show_top_languages or language.code not in top_languages_codes
        ]


class TutorAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'tutor'

    def get_list(self):
        return DoctorateAutocompleteService.autocomplete_tutors(
            person=self.request.user.person,
            search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=result.global_id,
                text="{result.first_name} {result.last_name}".format(result=result),
            )
            for result in results
        ]


class PersonAutocomplete(TutorAutocomplete):
    urlpatterns = 'person'

    def get_list(self):
        return DoctorateAutocompleteService.autocomplete_persons(
            person=self.request.user.person,
            search=self.q,
        )


class InstituteAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'institute'

    def get_list(self):
        # Return a list of UCL institutes whose title / acronym is specified by the user
        return EntitiesService.get_ucl_entities(
            limit=10,
            person=self.request.user.person,
            entity_type=[
                EntiteTypeEnum(INSTITUTE),
            ],
            search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=entity.uuid,
                text=format_entity_title(entity=entity),
            )
            for entity in results
        ]


class LearningUnitYearsAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'learning-unit-years'

    def get_list(self):
        return DoctorateAutocompleteService.autocomplete_learning_unit_years(
            person=self.request.user.person,
            year=self.forwarded['academic_year'],
            acronym_search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=result['acronym'],
                text=f"{result['acronym']} - {result['title']}",
            )
            for result in results
        ]


class SuperiorInstituteAutocomplete(LoginRequiredMixin, PaginatedAutocompleteMixin, autocomplete.Select2ListView):
    urlpatterns = 'superior-institute'

    def get_list(self):
        additional_filters = {}
        country = self.forwarded.get('country')
        is_belgian = self.forwarded.get('is_belgian') in TRUTHY_VALUES
        if country:
            additional_filters['country_iso_code'] = country
        elif is_belgian:
            additional_filters['country_iso_code'] = BE_ISO_CODE
        additional_filters.update(self.get_webservice_pagination_kwargs())

        universities = UniversityService.get_universities(
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )
        total_universities = universities.count
        universities = universities.results

        # In case we ran out of universities to show
        if len(universities) < self.paginate_by or additional_filters['offset'] >= total_universities:
            if universities:
                # We only get the amount we need to hit the limit so that later calls can just substract the total
                # to get the current offset.
                additional_filters['limit'] = self.paginate_by - total_universities % self.paginate_by
                additional_filters['offset'] = 0
            else:
                additional_filters['offset'] -= total_universities
            superior_non_universities = SuperiorNonUniversityService.get_superior_non_universities(
                person=self.request.user.person,
                search=self.q,
                active=True,
                **additional_filters,
            )
        else:
            superior_non_universities = []

        return sorted(
            itertools.chain(universities, superior_non_universities),
            key=lambda institute: institute.name,
        )

    def results(self, results):
        return [
            dict(
                id=result.uuid,
                text=format_school_title(result),
                type=StudyType.UNIVERSITY.name if isinstance(result, University) else StudyType.NON_UNIVERSITY.name,
            )
            for result in results
        ]
