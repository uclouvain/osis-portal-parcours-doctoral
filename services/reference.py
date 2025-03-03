# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import lru_cache
from typing import List

from django.http import Http404
from osis_reference_sdk import ApiClient, ApiException
from osis_reference_sdk.api import (
    academic_years_api,
    countries_api,
    languages_api,
    superior_non_universities_api,
    universities_api,
)
from osis_reference_sdk.model.academic_year import AcademicYear

from frontoffice.settings.osis_sdk import reference as reference_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from parcours_doctoral.contrib.enums.diploma import StudyType
from parcours_doctoral.services.mixins import ServiceMeta


class CountriesAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return countries_api.CountriesApi(ApiClient(configuration=api_config))


class CountriesService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_countries(cls, person=None, *args, **kwargs):
        return (
            CountriesAPIClient()
            .countries_list(
                active=True,
                *args,
                **kwargs,
                **build_mandatory_auth_headers(person),
            )
            .results
        )

    @classmethod
    @lru_cache()
    def get_country(cls, person=None, *args, **kwargs):
        countries = (
            CountriesAPIClient()
            .countries_list(
                active=True,
                *args,
                **kwargs,
                **build_mandatory_auth_headers(person),
                limit=1,
            )
            .results
        )
        if not countries:
            return None
        return countries[0]


class AcademicYearAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return academic_years_api.AcademicYearsApi(ApiClient(configuration=api_config))


class AcademicYearService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_academic_years(cls, person) -> List[AcademicYear]:
        """Returns the academic years"""
        return (
            AcademicYearAPIClient()
            .get_academic_years(
                limit=100,
                **build_mandatory_auth_headers(person),
            )
            .results
        )


class LanguagesAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return languages_api.LanguagesApi(ApiClient(configuration=api_config))


class LanguageService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_languages(cls, person, *args, **kwargs):
        return (
            LanguagesAPIClient()
            .languages_list(
                limit=kwargs.pop('limit', 100),
                *args,
                **kwargs,
                **build_mandatory_auth_headers(person),
            )
            .results
        )

    @classmethod
    def get_language(cls, code, person=None):
        languages = (
            LanguagesAPIClient()
            .languages_list(
                limit=1,
                code=code,
                **build_mandatory_auth_headers(person),
            )
            .results
        )
        return languages[0] if languages else None


class SuperiorNonUniversityAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return superior_non_universities_api.SuperiorNonUniversitiesApi(ApiClient(configuration=api_config))


class SuperiorNonUniversityService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_superior_non_universities(cls, person, **kwargs):
        return (
            SuperiorNonUniversityAPIClient()
            .superior_non_universities_list(
                limit=kwargs.pop('limit', 100),
                **kwargs,
                **build_mandatory_auth_headers(person),
            )
            .results
        )

    @classmethod
    def get_superior_non_university(cls, person, uuid, **kwargs):
        return SuperiorNonUniversityAPIClient().superior_non_university_read(
            uuid=uuid,
            **kwargs,
            **build_mandatory_auth_headers(person),
        )


class UniversityAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return universities_api.UniversitiesApi(ApiClient(configuration=api_config))


class UniversityService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_universities(cls, person, **kwargs):
        return UniversityAPIClient().universities_list(
            limit=kwargs.pop('limit', 100),
            **kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_university(cls, person, uuid, **kwargs):
        return UniversityAPIClient().university_read(
            uuid=uuid,
            **kwargs,
            **build_mandatory_auth_headers(person),
        )


class SuperiorInstituteService:
    @classmethod
    def get_superior_institute(cls, person, uuid, study_type=''):
        if study_type == StudyType.UNIVERSITY.name:
            return UniversityService.get_university(person=person, uuid=uuid)
        elif study_type == StudyType.NON_UNIVERSITY.name:
            return SuperiorNonUniversityService.get_superior_non_university(person=person, uuid=uuid)
        else:
            # We don't know so we need to check the two services
            try:
                return UniversityService.get_university(person=person, uuid=uuid)
            except Http404:
                return SuperiorNonUniversityService.get_superior_non_university(person=person, uuid=uuid)
