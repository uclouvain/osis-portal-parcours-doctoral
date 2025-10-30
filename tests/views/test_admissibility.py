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
import datetime

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.admissibility_dto import AdmissibilityDTO
from osis_parcours_doctoral_sdk.model.admissibility_minutes_canvas import (
    AdmissibilityMinutesCanvas,
)
from osis_parcours_doctoral_sdk.model.submit_admissibility import SubmitAdmissibility

from base.tests.factories.person import PersonFactory
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.forms.admissibility import AdmissibilityForm
from parcours_doctoral.contrib.forms.private_defense import PrivateDefenseForm
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class AdmissibilityDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:admissibility", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2025, 11, 1),
                date_envoi_manuscrit=datetime.date(2025, 11, 10),
            ),
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2024, 11, 1),
                date_envoi_manuscrit=datetime.date(2024, 11, 10),
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_admissibility'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_admissibility(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the admissibilities information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertIsNotNone(response.context.get('all_admissibilities'))
        self.assertEqual(response.context.get('all_admissibilities')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_admissibilities')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_admissibility'))
        self.assertEqual(response.context.get('current_admissibility').uuid, 'p1')

    def test_get_no_admissibility(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertEqual(response.context.get('all_admissibilities'), [])

        self.assertIsNone(response.context.get('current_admissibility'))


class PrivateDefenseFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url("parcours_doctoral:update:admissibility", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:admissibility", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2025, 11, 1),
                date_envoi_manuscrit=datetime.date(2025, 11, 10),
            ),
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2024, 11, 1),
                date_envoi_manuscrit=datetime.date(2024, 11, 10),
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_admissibility'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_admissibility(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the admissibilities information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertIsNotNone(response.context.get('all_admissibilities'))
        self.assertEqual(response.context.get('all_admissibilities')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_admissibilities')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_admissibility'))
        self.assertEqual(response.context.get('current_admissibility').uuid, 'p1')

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, AdmissibilityForm)

        self.assertEqual(form['titre_these'].value(), 'Title')
        self.assertEqual(form['date_decision'].value(), datetime.date(2025, 11, 1))
        self.assertEqual(form['date_envoi_manuscrit'].value(), datetime.date(2025, 11, 10))

    def test_get_no_admissibility(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertEqual(response.context.get('all_admissibilities'), [])

        self.assertIsNone(response.context.get('current_admissibility'))

        # Load the form
        form = response.context['form']

        self.assertEqual(form['titre_these'].value(), 'Title')
        self.assertEqual(form['date_decision'].value(), None)
        self.assertEqual(form['date_envoi_manuscrit'].value(), None)

    def test_post_a_admissibility_with_complete_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={
                'titre_these': 'My new title',
                'date_decision': datetime.date(2025, 12, 1),
                'date_envoi_manuscrit': datetime.date(2025, 12, 10),
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_admissibility.assert_called()
        self.mock_doctorate_api.return_value.submit_admissibility.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_admissibility=SubmitAdmissibility._new_from_openapi_data(
                titre_these='My new title',
                date_decision=datetime.date(2025, 12, 1),
                date_envoi_manuscrit=datetime.date(2025, 12, 10),
            ),
            **self.api_default_params,
        )

    def test_post_a_admissibility_with_minimal_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=None,
                date_envoi_manuscrit=None,
            ),
        ]
        response = self.client.post(
            self.url,
            data={
                'titre_these': 'My new title',
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_admissibility.assert_called()
        self.mock_doctorate_api.return_value.submit_admissibility.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_admissibility=SubmitAdmissibility._new_from_openapi_data(
                titre_these='My new title',
                date_decision=None,
                date_envoi_manuscrit=None,
            ),
            **self.api_default_params,
        )

    def test_post_invalid_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=None,
                date_envoi_manuscrit=None,
            ),
        ]

        response = self.client.post(
            self.url,
            data={},
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 1)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('titre_these'))


class AdmissibilityMinutesCanvasViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:admissibility-minutes-canvas", pk=cls.doctorate_uuid)
        cls.project_url = resolve_url('parcours_doctoral:project', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_admissibility_minutes_canvas.return_value = (
            AdmissibilityMinutesCanvas._from_openapi_data(url=self.project_url)
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_admissibility_minutes_canvas'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_redirect_to_the_specific_url(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertRedirects(response=response, expected_url=self.project_url, fetch_redirect_response=False)
