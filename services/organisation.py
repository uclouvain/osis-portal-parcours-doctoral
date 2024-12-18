# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_organisation_sdk import ApiClient, ApiException
from osis_organisation_sdk.api import entites_api

from frontoffice.settings.osis_sdk import organisation as organisation_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from parcours_doctoral.constants import UCL_CODE
from parcours_doctoral.services.mixins import ServiceMeta


class EntitiesAPIClient:
    def __new__(cls):
        api_config = organisation_sdk.build_configuration()
        return entites_api.EntitesApi(ApiClient(configuration=api_config))


class EntitiesService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_ucl_entities(cls, person, entity_type, *args, **kwargs):
        return (
            EntitiesAPIClient()
            .get_entities(
                entity_type=entity_type,
                organisation_code=UCL_CODE,
                *args,
                **kwargs,
                **build_mandatory_auth_headers(person),
            )
            .results
        )

    @classmethod
    def get_ucl_entity(cls, person, uuid, *args, **kwargs):
        return EntitiesAPIClient().get_entity(
            uuid=uuid,
            organisation_code=UCL_CODE,
            *args,
            **kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_ucl_entity_addresses(cls, person, uuid, *args, **kwargs):
        # TODO will become (again) a list of results
        offset = 0
        return [
            EntitiesAPIClient().get_entity_addresses(
                organisation_code=UCL_CODE,
                uuid=uuid,
                offset=offset,
                *args,
                **kwargs,
                **build_mandatory_auth_headers(person),
            )
        ]
        # has_next = True
        # results = []
        # while has_next:
        #     paginated_results = EntitiesAPIClient().get_entity_addresses(
        #         organisation_code=UCL_CODE,
        #         uuid=uuid,
        #         offset=offset,
        #         *args,
        #         **kwargs,
        #         **build_mandatory_auth_headers(person)
        #     )
        #     has_next = paginated_results.next is not None
        #     results += paginated_results.results
        #     offset = len(results)
        #
        # return results
