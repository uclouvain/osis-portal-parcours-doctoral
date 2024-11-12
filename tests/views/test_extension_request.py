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
import datetime
from unittest.mock import Mock

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.model.action_link import ActionLink

from base.tests.factories.person import PersonFactory
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class ExtensionRequestDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:extension-request", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = Mock(
            uuid='c1',
            date_limite='2022-06-10',
            date='2022-04-03',
            rapport_recherche=['f1'],
            avis_renouvellement_mandat_recherche=['f2'],
            proces_verbal_ca=['f3'],
            to_dict=dict(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=['f1'],
                avis_renouvellement_mandat_recherche=['f2'],
                proces_verbal_ca=['f3'],
            ),
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_confirmation_extension'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_confirmation_paper(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertContains(response, "osis-document.umd.min.js")
        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, 'c1')

    def test_get_no_confirmation_paper(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = None

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNone(response.context.get('confirmation_paper'))


class ExtensionRequestFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.promoter = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:update:extension-request", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = Mock(
            uuid='c1',
            date_limite='2022-06-10',
            date='2022-04-03',
            rapport_recherche=['f1'],
            avis_renouvellement_mandat_recherche=['f2'],
            proces_verbal_ca=['f3'],
            demande_prolongation=Mock(
                nouvelle_echeance='2023-01-01',
                justification_succincte='My reason',
                lettre_justification=['f2'],
            ),
            to_dict=dict(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=['f1'],
                avis_renouvellement_mandat_recherche=['f2'],
                proces_verbal_ca=['f3'],
                demande_prolongation=dict(
                    nouvelle_echeance='2023-01-01',
                    justification_succincte='My reason',
                    lettre_justification=['f2'],
                ),
            ),
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_confirmation_extension'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_confirmation_paper(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)
        self.assertContains(response, "osis-document.umd.min.js")

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        # Initialize the form
        self.assertEqual(response.context.get('form').initial['nouvelle_echeance'], '2023-01-01')
        self.assertEqual(response.context.get('form').initial['justification_succincte'], 'My reason')
        self.assertEqual(response.context.get('form').initial['lettre_justification'], ['f2'])

    def test_get_no_confirmation_paper(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = None

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('form').initial, {})

    def test_post_a_confirmation_paper(self):
        self.client.force_login(self.person.user)

        self.client.post(
            self.url,
            data={
                'nouvelle_echeance': datetime.date(2024, 1, 1),
                'justification_succincte': 'My second reason',
                'lettre_justification_0': ['f22'],
            },
        )
        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_confirmation_paper_extension_request.assert_called()
        self.mock_doctorate_api.return_value.submit_confirmation_paper_extension_request.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_confirmation_paper_extension_request_command={
                'nouvelle_echeance': datetime.date(2024, 1, 1),
                'justification_succincte': 'My second reason',
                'lettre_justification': ['f22'],
            },
            **self.api_default_params,
        )
