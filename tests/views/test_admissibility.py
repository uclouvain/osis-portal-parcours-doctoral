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
import uuid

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.models.action_link import ActionLink
from osis_parcours_doctoral_sdk.models.admissibility_dto import AdmissibilityDTO
from osis_parcours_doctoral_sdk.models.admissibility_minutes_canvas import (
    AdmissibilityMinutesCanvas,
)
from osis_parcours_doctoral_sdk.models.submit_admissibility import SubmitAdmissibility
from osis_parcours_doctoral_sdk.models.submit_admissibility_minutes_and_opinions import (
    SubmitAdmissibilityMinutesAndOpinions,
)

from base.tests.factories.person import PersonFactory
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.forms.admissibility import (
    AdmissibilityForm,
    JuryMemberAdmissibilityForm,
)
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
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2025, 11, 1),
                date_envoi_manuscrit=datetime.date(2025, 11, 10),
            ),
            AdmissibilityDTO(
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
        self.mock_doctorate_object.links.retrieve_admissibility = ActionLink(
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

        # Load the admissibility information
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
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                proces_verbal=[],
                canevas_proces_verbal=[],
                avis_jury=[],
                date_decision=datetime.date(2025, 11, 1),
                date_envoi_manuscrit=datetime.date(2025, 11, 10),
            ),
            AdmissibilityDTO(
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
        self.mock_doctorate_object.links.update_admissibility = ActionLink(
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

        self.assertEqual(form['titre_these'].value(), 'Thesis title 1')
        self.assertEqual(form['date_decision'].value(), datetime.date(2025, 11, 1))
        self.assertEqual(form['date_envoi_manuscrit'].value(), datetime.date(2025, 11, 10))

    def test_get_no_admissibility(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the admissibility information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertEqual(response.context.get('all_admissibilities'), [])

        self.assertIsNone(response.context.get('current_admissibility'))

        # Load the form
        form = response.context['form']

        self.assertEqual(form['titre_these'].value(), 'Thesis title 1')
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
            submit_admissibility=SubmitAdmissibility(
                titre_these='My new title',
                date_decision=datetime.date(2025, 12, 1),
                date_envoi_manuscrit=datetime.date(2025, 12, 10),
            ),
            **self.api_default_params,
        )

    def test_post_a_admissibility_with_minimal_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO(
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
            submit_admissibility=SubmitAdmissibility(
                titre_these='My new title',
                date_decision=None,
                date_envoi_manuscrit=None,
            ),
            **self.api_default_params,
        )

    def test_post_invalid_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO(
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
            AdmissibilityMinutesCanvas(url=self.project_url)
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links.retrieve_admissibility_minutes_canvas = ActionLink(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_redirect_to_the_specific_url(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertRedirects(response=response, expected_url=self.project_url, fetch_redirect_response=False)


class AdmissibilityFormViewForPromoterTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.promoter_person = PersonFactory(global_id='12345')
        cls.url = resolve_url("parcours_doctoral:update:admissibility", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:admissibility", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                avis_jury=['file-11-uuid'],
                proces_verbal=['file-12-uuid'],
                canevas_proces_verbal=[],
                date_decision=datetime.date(2025, 1, 1),
                date_envoi_manuscrit=datetime.date(2025, 1, 2),
            ),
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                avis_jury=['file-21-uuid'],
                proces_verbal=['file-22-uuid'],
                canevas_proces_verbal=[],
                date_decision=datetime.date(2024, 1, 1),
                date_envoi_manuscrit=datetime.date(2024, 1, 2),
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.promoter_person.user)
        self.mock_doctorate_object.links.submit_admissibility_minutes_and_opinions = ActionLink(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_admissibility(self):
        self.client.force_login(self.promoter_person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the admissibility information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertIsNotNone(response.context.get('all_admissibilities'))
        self.assertEqual(response.context.get('all_admissibilities')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_admissibilities')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_admissibility'))
        self.assertEqual(response.context.get('current_admissibility').uuid, 'p1')

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, JuryMemberAdmissibilityForm)

        self.assertEqual(form['avis_jury'].value(), ['file-11-uuid'])
        self.assertEqual(form['proces_verbal'].value(), ['file-12-uuid'])

    def test_get_no_admissibility(self):
        self.client.force_login(self.promoter_person.user)
        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the admissibilities information
        self.mock_doctorate_api.return_value.retrieve_admissibilities.assert_called()

        self.assertEqual(response.context.get('all_admissibilities'), [])

        self.assertIsNone(response.context.get('current_admissibility'))

        # Load the form
        form = response.context['form']

        self.assertEqual(form['proces_verbal'].value(), [])

    def test_post_the_admissibility_minutes(self):
        self.client.force_login(self.promoter_person.user)

        response = self.client.post(
            self.url,
            data={
                'avis_jury_0': ['file-uuid-12a'],
                'proces_verbal_0': ['file-uuid-12b'],
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_admissibility_minutes_and_opinions.assert_called()
        self.mock_doctorate_api.return_value.submit_admissibility_minutes_and_opinions.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_admissibility_minutes_and_opinions=SubmitAdmissibilityMinutesAndOpinions(
                avis_jury=['file-uuid-12a'],
                proces_verbal=['file-uuid-12b'],
            ),
            **self.api_default_params,
        )


class AdmissibilityMinutesViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.first_admissibility_uuid = uuid.uuid4()
        cls.second_admissibility_uuid = uuid.uuid4()

        cls.person = PersonFactory()
        cls.url = resolve_url(
            'parcours_doctoral:admissibility-minutes',
            pk=cls.doctorate_uuid,
            admissibility_id=cls.first_admissibility_uuid,
        )
        cls.admissibility_url = resolve_url('parcours_doctoral:admissibility', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value = [
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid=str(self.first_admissibility_uuid),
                est_active=True,
                avis_jury=[],
                proces_verbal=['file-1'],
                canevas_proces_verbal=[],
            ),
            AdmissibilityDTO(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid=str(self.second_admissibility_uuid),
                est_active=False,
                avis_jury=[],
                proces_verbal=[],
                canevas_proces_verbal=[],
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links.retrieve_admissibility = ActionLink(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_redirect_to_the_minutes_url_if_any(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl.com/document/file/foobar',
            fetch_redirect_response=False,
        )

    def test_redirect_to_the_admissibilitys_url_if_no_minutes_to_redirect(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_admissibilities.return_value[0].proces_verbal = []

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url=self.admissibility_url,
            fetch_redirect_response=False,
        )
