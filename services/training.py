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
from importlib import import_module

import osis_parcours_doctoral_sdk
from django.http import HttpResponseBadRequest
from osis_parcours_doctoral_sdk.api import doctorate_api
from osis_parcours_doctoral_sdk.model.type_enum import TypeEnum

from frontoffice.settings.osis_sdk import parcours_doctoral as parcours_doctoral_sdk
from frontoffice.settings.osis_sdk.utils import (
    ApiBusinessException,
    MultipleApiBusinessException,
    build_mandatory_auth_headers,
)
from parcours_doctoral.services.mixins import ServiceMeta
from parcours_doctoral.utils.utils import to_snake_case

OBJECT_TYPE_PAPER = 'Paper'


class APIClient:
    def __new__(cls):
        api_config = parcours_doctoral_sdk.build_configuration()
        return doctorate_api.DoctorateApi(osis_parcours_doctoral_sdk.ApiClient(configuration=api_config))


class ActivityApiBusinessException(ApiBusinessException):
    def __init__(self, activite_id=None, **kwargs):
        self.activite_id = activite_id
        super().__init__(**kwargs)


class DoctorateTrainingService(metaclass=ServiceMeta):
    api_exception_cls = osis_parcours_doctoral_sdk.ApiException

    @classmethod
    def get_config(cls, person, uuid):
        return APIClient().retrieve_doctoral_training_config(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_doctoral_training(cls, person, uuid):
        return APIClient().list_doctoral_training(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_complementary_training(cls, person, uuid):
        return APIClient().list_complementary_training(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_course_enrollment(cls, person, uuid):
        return APIClient().list_course_enrollment(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_assessment_enrollment(cls, person, uuid):
        return APIClient().list_inscription_evaluation_dtos(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_assessment_enrollment(cls, person, uuid, enrollment_uuid):
        return APIClient().retrieve_inscription_evaluation_dto(
            uuid=uuid,
            enrollment_uuid=enrollment_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_activity(cls, person, doctorate_uuid, activity_uuid):
        return APIClient().retrieve_training(
            uuid=doctorate_uuid,
            activity_id=activity_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_activity(cls, person, uuid, **kwargs):
        return APIClient().create_doctoral_training(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
            doctoral_training_activity=cls._get_activity(kwargs),
        )

    @classmethod
    def update_activity(cls, person, doctorate_uuid, activity_uuid, **kwargs):
        return APIClient().update_training(
            uuid=doctorate_uuid,
            activity_id=activity_uuid,
            **build_mandatory_auth_headers(person),
            doctoral_training_activity=cls._get_activity(kwargs),
        )

    @classmethod
    def _get_activity(cls, kwargs):
        class_name = kwargs["object_type"]
        module = import_module(f'osis_parcours_doctoral_sdk.model.{to_snake_case(class_name)}')
        activity_class = getattr(module, class_name)
        return activity_class(**kwargs)

    @classmethod
    def submit_activities(cls, person, uuid, **kwargs):
        try:
            return APIClient().submit_training(
                uuid=uuid,
                **build_mandatory_auth_headers(person),
                doctoral_training_batch=kwargs,
            )
        except osis_parcours_doctoral_sdk.ApiException as api_exception:
            # We need special API handling to add activity info
            if api_exception.status == HttpResponseBadRequest.status_code:
                import json

                api_business_exceptions = set()

                body_json = json.loads(api_exception.body)
                for key, exceptions in body_json.items():
                    api_business_exceptions |= {ActivityApiBusinessException(**exception) for exception in exceptions}
                raise MultipleApiBusinessException(exceptions=api_business_exceptions)
            raise api_exception

    @classmethod
    def delete_activity(cls, person, doctorate_uuid, activity_uuid):
        return APIClient().destroy_training(
            uuid=doctorate_uuid,
            activity_id=activity_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def assent_activity(cls, person, doctorate_uuid, activity_uuid, **kwargs):
        return APIClient().assent_training(
            uuid=doctorate_uuid,
            activity_id=activity_uuid,
            **build_mandatory_auth_headers(person),
            **kwargs,
            doctoral_training_assent=kwargs,
        )
