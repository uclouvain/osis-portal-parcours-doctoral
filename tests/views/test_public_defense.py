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
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.public_defense_minutes_canvas import (
    PublicDefenseMinutesCanvas,
)
from osis_parcours_doctoral_sdk.model.submit_public_defense import SubmitPublicDefense
from osis_parcours_doctoral_sdk.model.submit_public_defense_minutes import (
    SubmitPublicDefenseMinutes,
)

from base.tests.factories.person import PersonFactory
from osis_common.utils.datetime import get_tzinfo
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.forms import PNG_MIME_TYPE
from parcours_doctoral.contrib.forms.public_defense import (
    PromoterPublicDefenseForm,
    PublicDefenseForm,
)
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class PublicDefenseDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:public-defense", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_public_defense'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_public_defense(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)


class PublicDefenseFormViewTestCase(BaseDoctorateTestCase):
    mime_type = PNG_MIME_TYPE

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url("parcours_doctoral:update:public-defense", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:public-defense", pk=cls.doctorate_uuid)

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_public_defense'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_public_defense(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, PublicDefenseForm)

        self.assertEqual(form['langue'].value(), 'FR')
        self.assertEqual(form['date_heure'].value(), datetime.datetime(2024, 2, 2, 11, 30))
        self.assertEqual(form['lieu'].value(), 'Louvain-La-Neuve')
        self.assertEqual(form['local_deliberation'].value(), 'D1')
        self.assertEqual(form['resume_annonce'].value(), 'Announcement summary')
        self.assertEqual(form['photo_annonce'].value(), [])

    def test_post_a_public_defense_with_complete_data(self):
        self.client.force_login(self.person.user)

        file_uuid = str(uuid.uuid4())

        response = self.client.post(
            self.url,
            data={
                'langue': 'FR',
                'date_heure_0': '01/01/2026',
                'date_heure_1': '11:00',
                'lieu': 'Louvain',
                'local_deliberation': 'D2',
                'resume_annonce': 'New summary',
                'photo_annonce_0': [file_uuid],
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_public_defense.assert_called()
        self.mock_doctorate_api.return_value.submit_public_defense.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_public_defense=SubmitPublicDefense._new_from_openapi_data(
                langue='FR',
                date_heure=datetime.datetime(2026, 1, 1, 11, tzinfo=get_tzinfo()),
                lieu='Louvain',
                local_deliberation='D2',
                resume_annonce='New summary',
                photo_annonce=[file_uuid],
            ),
            **self.api_default_params,
        )

    def test_post_invalid_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={},
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 3)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('langue'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('date_heure'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('photo_annonce'))


class PublicDefenseMinutesCanvasViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:public-defense-minutes-canvas", pk=cls.doctorate_uuid)
        cls.project_url = resolve_url('parcours_doctoral:project', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_public_defense_minutes_canvas.return_value = (
            PublicDefenseMinutesCanvas._from_openapi_data(url=self.project_url)
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_public_defense_minutes_canvas'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_redirect_to_the_specific_url(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertRedirects(response=response, expected_url=self.project_url, fetch_redirect_response=False)


class PublicDefenseFormViewForPromoterTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.promoter_person = PersonFactory(global_id='12345')
        cls.url = resolve_url('parcours_doctoral:update:public-defense', pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url('parcours_doctoral:public-defense', pk=cls.doctorate_uuid)

    def test_get_no_permission(self):
        self.client.force_login(self.promoter_person.user)
        self.mock_doctorate_object.links['submit_public_defense_minutes'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_public_defense(self):
        self.client.force_login(self.promoter_person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, PromoterPublicDefenseForm)

        self.assertEqual(form['proces_verbal'].value(), ['minutes-uuid'])

    def test_post_the_public_defense_minutes(self):
        self.client.force_login(self.promoter_person.user)

        response = self.client.post(
            self.url,
            data={'proces_verbal_0': ['file-uuid-3']},
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_public_defense_minutes.assert_called()
        self.mock_doctorate_api.return_value.submit_public_defense_minutes.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_public_defense_minutes=SubmitPublicDefenseMinutes._new_from_openapi_data(
                proces_verbal=['file-uuid-3'],
            ),
            **self.api_default_params,
        )
