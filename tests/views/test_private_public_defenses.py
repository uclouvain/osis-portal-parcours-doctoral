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
from osis_parcours_doctoral_sdk.models.private_defense_dto import PrivateDefenseDTO
from osis_parcours_doctoral_sdk.models.submit_private_public_defenses import (
    SubmitPrivatePublicDefenses,
)
from osis_parcours_doctoral_sdk.models.submit_private_public_defenses_minutes import (
    SubmitPrivatePublicDefensesMinutes,
)

from base.tests.factories.person import PersonFactory
from osis_common.utils.datetime import get_tzinfo
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.forms import PNG_MIME_TYPE
from parcours_doctoral.contrib.forms.private_public_defenses import (
    PrivatePublicDefensesForm,
    PromoterPrivatePublicDefensesForm,
)
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class PrivatePublicDefensesDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url("parcours_doctoral:private-public-defenses", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = [
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                titre_these='Thesis title 1',
                lieu='Louvain-La-Neuve',
                proces_verbal=[],
                canevas_proces_verbal=[],
            ),
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                titre_these='Thesis title 2',
                lieu='Louvain-La-Neuve',
                proces_verbal=[],
                canevas_proces_verbal=[],
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_private_public_defenses'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_private_public_defenses(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertIsNotNone(response.context.get('all_private_defenses'))
        self.assertEqual(response.context.get('all_private_defenses')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_private_defenses')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_private_defense'))
        self.assertEqual(response.context.get('current_private_defense').uuid, 'p1')

    def test_get_no_private_public_defenses(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertEqual(response.context.get('all_private_defenses'), [])

        self.assertIsNone(response.context.get('current_private_defense'))


class PrivateDefenseFormViewTestCase(BaseDoctorateTestCase):
    mime_type = PNG_MIME_TYPE

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url("parcours_doctoral:update:private-public-defenses", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:private-public-defenses", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = [
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                titre_these='Thesis title 1',
                lieu='Louvain-La-Neuve',
                proces_verbal=[],
                canevas_proces_verbal=[],
                date_heure=datetime.datetime(2025, 1, 1, 10),
                date_envoi_manuscrit=datetime.date(2025, 1, 1),
            ),
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                titre_these='Thesis title 2',
                lieu='Louvain-La-Neuve',
                proces_verbal=[],
                canevas_proces_verbal=[],
                date_heure=datetime.datetime(2024, 1, 1, 10),
                date_envoi_manuscrit=datetime.date(2024, 1, 1),
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_private_public_defenses'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_private_public_defenses(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertIsNotNone(response.context.get('all_private_defenses'))
        self.assertEqual(response.context.get('all_private_defenses')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_private_defenses')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_private_defense'))
        self.assertEqual(response.context.get('current_private_defense').uuid, 'p1')

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, PrivatePublicDefensesForm)

        self.assertEqual(form['titre_these'].value(), 'Thesis title 1')
        self.assertEqual(form['date_heure_defense_privee'].value(), datetime.datetime(2025, 1, 1, 10))
        self.assertEqual(form['lieu_defense_privee'].value(), 'Louvain-La-Neuve')
        self.assertEqual(form['date_envoi_manuscrit'].value(), datetime.date(2025, 1, 1))
        self.assertEqual(form['langue_soutenance_publique'].value(), 'FR')
        self.assertEqual(form['date_heure_soutenance_publique'].value(), datetime.datetime(2024, 2, 2, 11, 30))
        self.assertEqual(form['lieu_soutenance_publique'].value(), 'Louvain-La-Neuve')
        self.assertEqual(form['local_deliberation'].value(), 'D1')
        self.assertEqual(form['resume_annonce'].value(), 'Announcement summary')
        self.assertEqual(form['photo_annonce'].value(), [])

    def test_get_with_no_private_defense(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertEqual(response.context.get('all_private_defenses'), [])

        self.assertIsNone(response.context.get('current_private_defense'))

        # Load the form
        form = response.context['form']

        self.assertEqual(form['titre_these'].value(), 'Thesis title 1')
        self.assertEqual(form['date_heure_defense_privee'].value(), None)
        self.assertEqual(form['lieu_defense_privee'].value(), None)
        self.assertEqual(form['date_envoi_manuscrit'].value(), None)

    def test_post_complete_data(self):
        self.client.force_login(self.person.user)

        file_uuid = str(uuid.uuid4())

        response = self.client.post(
            self.url,
            data={
                'titre_these': 'My new title',
                'date_heure_defense_privee_0': '01/01/2026',
                'date_heure_defense_privee_1': '11:00',
                'lieu_defense_privee': 'New place',
                'date_envoi_manuscrit': datetime.date(2025, 12, 1),
                'langue_soutenance_publique': 'FR',
                'date_heure_soutenance_publique_0': '02/01/2026',
                'date_heure_soutenance_publique_1': '12:00',
                'lieu_soutenance_publique': 'Louvain',
                'local_deliberation': 'D2',
                'resume_annonce': 'New summary',
                'photo_annonce_0': [file_uuid],
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_private_public_defenses.assert_called()
        self.mock_doctorate_api.return_value.submit_private_public_defenses.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_private_public_defenses=SubmitPrivatePublicDefenses._new_from_openapi_data(
                titre_these='My new title',
                date_heure_defense_privee=datetime.datetime(2026, 1, 1, 11, tzinfo=get_tzinfo()),
                lieu_defense_privee='New place',
                date_envoi_manuscrit=datetime.date(2025, 12, 1),
                langue_soutenance_publique='FR',
                date_heure_soutenance_publique=datetime.datetime(2026, 1, 2, 12, tzinfo=get_tzinfo()),
                lieu_soutenance_publique='Louvain',
                local_deliberation='D2',
                resume_annonce='New summary',
                photo_annonce=[file_uuid],
            ),
            **self.api_default_params,
        )

    def test_post_a_private_defense_with_minimal_data(self):
        self.client.force_login(self.person.user)

        file_uuid = str(uuid.uuid4())

        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = [
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                titre_these='',
                lieu='',
                proces_verbal=[],
                canevas_proces_verbal=[],
                date_heure=None,
                date_envoi_manuscrit=None,
            ),
        ]
        response = self.client.post(
            self.url,
            data={
                'titre_these': 'My new title',
                'date_heure_defense_privee_0': '01/01/2026',
                'date_heure_defense_privee_1': '11:00',
                'langue_soutenance_publique': 'FR',
                'date_heure_soutenance_publique_0': '02/01/2026',
                'date_heure_soutenance_publique_1': '12:00',
                'photo_annonce_0': [file_uuid],
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_private_public_defenses.assert_called()
        self.mock_doctorate_api.return_value.submit_private_public_defenses.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_private_public_defenses=SubmitPrivatePublicDefenses._new_from_openapi_data(
                titre_these='My new title',
                date_heure_defense_privee=datetime.datetime(2026, 1, 1, 11, tzinfo=get_tzinfo()),
                lieu_defense_privee='',
                date_envoi_manuscrit=None,
                langue_soutenance_publique='FR',
                date_heure_soutenance_publique=datetime.datetime(2026, 1, 2, 12, tzinfo=get_tzinfo()),
                lieu_soutenance_publique='',
                local_deliberation='',
                resume_annonce='',
                photo_annonce=[file_uuid],
            ),
            **self.api_default_params,
        )

    def test_post_invalid_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = [
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                titre_these='',
                lieu='',
                proces_verbal=[],
                canevas_proces_verbal=[],
                date_heure=None,
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

        self.assertEqual(len(form.errors), 5)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('titre_these'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('date_heure_defense_privee'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('langue_soutenance_publique'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('date_heure_soutenance_publique'))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('photo_annonce'))


class PrivatePublicDefensesFormViewForPromoterTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.promoter_person = PersonFactory(global_id='12345')
        cls.url = resolve_url("parcours_doctoral:update:private-public-defenses", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:private-public-defenses", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = [
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p1',
                est_active=True,
                titre_these='Thesis title 1',
                lieu='Louvain-La-Neuve',
                proces_verbal=['file-1-uuid'],
                canevas_proces_verbal=[],
                date_heure=datetime.datetime(2025, 1, 1, 10),
                date_envoi_manuscrit=datetime.date(2025, 1, 1),
            ),
            PrivateDefenseDTO._from_openapi_data(
                parcours_doctoral_uuid=self.doctorate_uuid,
                uuid='p2',
                est_active=False,
                titre_these='Thesis title 2',
                lieu='Louvain-La-Neuve',
                proces_verbal=['file-2-uuid'],
                canevas_proces_verbal=[],
                date_heure=datetime.datetime(2024, 1, 1, 10),
                date_envoi_manuscrit=datetime.date(2024, 1, 1),
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.promoter_person.user)
        self.mock_doctorate_object.links['submit_private_public_defenses_minutes'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_page(self):
        self.client.force_login(self.promoter_person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertIsNotNone(response.context.get('all_private_defenses'))
        self.assertEqual(response.context.get('all_private_defenses')[0].uuid, 'p1')
        self.assertEqual(response.context.get('all_private_defenses')[1].uuid, 'p2')

        self.assertIsNotNone(response.context.get('current_private_defense'))
        self.assertEqual(response.context.get('current_private_defense').uuid, 'p1')

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, PromoterPrivatePublicDefensesForm)

        self.assertEqual(form['proces_verbal_defense_privee'].value(), ['file-1-uuid'])
        self.assertEqual(form['proces_verbal_soutenance_publique'].value(), ['minutes-uuid'])

    def test_get_page_with_no_private_defense(self):
        self.client.force_login(self.promoter_person.user)
        self.mock_doctorate_api.return_value.retrieve_private_defenses.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the private defenses information
        self.mock_doctorate_api.return_value.retrieve_private_defenses.assert_called()

        self.assertEqual(response.context.get('all_private_defenses'), [])

        self.assertIsNone(response.context.get('current_private_defense'))

        # Load the form
        form = response.context['form']

        self.assertEqual(form['proces_verbal_defense_privee'].value(), [])
        self.assertEqual(form['proces_verbal_soutenance_publique'].value(), ['minutes-uuid'])

    def test_post_the_private_and_public_defenses_minutes(self):
        self.client.force_login(self.promoter_person.user)

        response = self.client.post(
            self.url,
            data={
                'proces_verbal_defense_privee_0': ['file-uuid-3'],
                'proces_verbal_soutenance_publique_0': ['file-uuid-4'],
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_private_public_defenses_minutes.assert_called()
        self.mock_doctorate_api.return_value.submit_private_public_defenses_minutes.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_private_public_defenses_minutes=SubmitPrivatePublicDefensesMinutes._new_from_openapi_data(
                proces_verbal_defense_privee=['file-uuid-3'],
                proces_verbal_soutenance_publique=['file-uuid-4'],
            ),
            **self.api_default_params,
        )
