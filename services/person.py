# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import person_api
from osis_admission_sdk.model.identification_dto import IdentificationDTO
from osis_admission_sdk.model.person_identification import PersonIdentification
from parcours_doctoral.services.mixins import ServiceMeta


class DoctoratePersonAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return person_api.PersonApi(ApiClient(configuration=api_config))


class DoctoratePersonService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    # Identification
    @classmethod
    def retrieve_identification_dto(cls, person) -> IdentificationDTO:
        return DoctoratePersonAPIClient().retrieve_identification_dto(
            **build_mandatory_auth_headers(person),
        )

    # Person
    @classmethod
    def retrieve_person(cls, person, uuid=None) -> PersonIdentification:
        if uuid:
            return DoctoratePersonAPIClient().retrieve_person_identification_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return DoctoratePersonAPIClient().retrieve_person_identification(
            **build_mandatory_auth_headers(person),
        )
