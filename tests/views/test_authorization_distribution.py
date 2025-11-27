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
from django.template.loader import render_to_string
from django.utils.translation.trans_real import gettext
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.authorization_distribution_dto import (
    AuthorizationDistributionDTO,
)
from osis_parcours_doctoral_sdk.model.send_authorization_distribution_to_promoter import (
    SendAuthorizationDistributionToPromoter,
)
from osis_parcours_doctoral_sdk.model.update_authorization_distribution import (
    UpdateAuthorizationDistribution,
)

from base.tests.factories.person import PersonFactory
from osis_common.utils.datetime import get_tzinfo
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.enums import TypeModalitesDiffusionThese
from parcours_doctoral.contrib.forms import EMPTY_CHOICE
from parcours_doctoral.contrib.forms.authorization_distribution import (
    AuthorizationDistributionForm,
)
from parcours_doctoral.contrib.views.autocomplete import LANGUAGE_UNDECIDED
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class AuthorizationDistributionDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url('parcours_doctoral:authorization-distribution', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.return_value = (
            AuthorizationDistributionDTO._from_openapi_data(
                uuid=self.doctorate_uuid,
                statut='DIFFUSION_NON_SOUMISE',
                sources_financement='Sources',
                resume_anglais='Summary in english',
                resume_autre_langue='Summary in another language',
                mots_cles=['word-1', 'word-2'],
                type_modalites_diffusion=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
                limitations_additionnelles_chapitres='Limitations',
                signataires=[],
                date_embargo=datetime.date(2025, 1, 1),
                modalites_diffusion_acceptees_le=datetime.date(2024, 1, 1),
            )
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_authorization_distribution'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_authorization_distribution(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the authorization distribution information
        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.assert_called()

        self.assertIsNotNone(response.context.get('authorization_distribution'))
        self.assertEqual(response.context.get('authorization_distribution').uuid, self.doctorate_uuid)


class AuthorizationDistributionFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:update:authorization-distribution', pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url('parcours_doctoral:authorization-distribution', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.return_value = (
            AuthorizationDistributionDTO._from_openapi_data(
                uuid=self.doctorate_uuid,
                statut='DIFFUSION_NON_SOUMISE',
                sources_financement='Sources',
                resume_anglais='Summary in english',
                resume_autre_langue='Summary in another language',
                mots_cles=['word-1', 'word-2'],
                type_modalites_diffusion=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
                limitations_additionnelles_chapitres='Limitations',
                signataires=[],
                date_embargo=datetime.date(2025, 1, 1),
                modalites_diffusion_acceptees_le=datetime.date(2024, 1, 1),
            )
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_authorization_distribution'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_authorization_distribution(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the authorization distribution information
        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.assert_called()

        self.assertIsNotNone(response.context.get('authorization_distribution'))
        self.assertEqual(response.context.get('authorization_distribution').uuid, self.doctorate_uuid)

        # Load the form
        form = response.context['form']

        self.assertIsInstance(form, AuthorizationDistributionForm)

        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.return_value = (
            AuthorizationDistributionDTO._from_openapi_data(
                uuid=self.doctorate_uuid,
                statut='DIFFUSION_NON_SOUMISE',
                sources_financement='Sources',
                resume_anglais='Summary in english',
                resume_autre_langue='Summary in another language',
                mots_cles=['word-1', 'word-2'],
                type_modalites_diffusion=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
                limitations_additionnelles_chapitres='Limitations',
                signataires=[],
                date_embargo=datetime.date(2025, 1, 1),
                modalites_diffusion_acceptees_le=datetime.date(2024, 1, 1),
            )
        )

        self.assertEqual(form['sources_financement'].value(), 'Sources')
        self.assertEqual(form['resume_anglais'].value(), 'Summary in english')
        self.assertEqual(form['resume_autre_langue'].value(), 'Summary in another language')
        self.assertEqual(form['langue_redaction_these'].value(), 'FR-BE')
        self.assertEqual(form['mots_cles'].value(), 'word-1,word-2')
        self.assertEqual(form['type_modalites_diffusion'].value(), TypeModalitesDiffusionThese.ACCES_EMBARGO.name)
        self.assertEqual(form['date_embargo'].value(), datetime.date(2025, 1, 1))
        self.assertEqual(form['limitations_additionnelles_chapitres'].value(), 'Limitations')
        self.assertEqual(form['accepter_conditions'].value(), True)

        self.assertEqual(form.fields['langue_redaction_these'].choices, [EMPTY_CHOICE[0], ('FR', 'Français')])

    def test_post_authorization_distribution_with_complete_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={
                'sources_financement': 'New sources',
                'resume_anglais': 'New summary in english',
                'resume_autre_langue': 'New summary in another language',
                'langue_redaction_these': 'FR',
                'mots_cles': 'word-3,word-4',
                'type_modalites_diffusion': TypeModalitesDiffusionThese.ACCES_RESTREINT.name,
                'date_embargo': datetime.date(2026, 2, 2).isoformat(),
                'limitations_additionnelles_chapitres': 'New limitations',
                'accepter_conditions': 'on',
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        accepted_content = render_to_string(
            'parcours_doctoral/includes/authorization_distribution/authorization_distribution_acceptation.html'
        )

        # Call the API with the right data
        self.mock_doctorate_api.return_value.send_authorization_distribution_to_promoter.assert_not_called()
        self.mock_doctorate_api.return_value.update_authorization_distribution.assert_called()
        self.mock_doctorate_api.return_value.update_authorization_distribution.assert_called_with(
            uuid=self.doctorate_uuid,
            update_authorization_distribution=UpdateAuthorizationDistribution._new_from_openapi_data(
                sources_financement='New sources',
                resume_anglais='New summary in english',
                resume_autre_langue='New summary in another language',
                langue_redaction_these='FR',
                mots_cles=['word-3', 'word-4'],
                type_modalites_diffusion=TypeModalitesDiffusionThese.ACCES_RESTREINT.name,
                date_embargo=None,
                limitations_additionnelles_chapitres='New limitations',
                modalites_diffusion_acceptees=accepted_content,
            ),
            **self.api_default_params,
        )

    def test_post_authorization_distribution_with_minimal_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.return_value = (
            AuthorizationDistributionDTO._from_openapi_data(
                uuid=self.doctorate_uuid,
                statut='DIFFUSION_NON_SOUMISE',
                sources_financement='',
                resume_anglais='',
                resume_autre_langue='',
                mots_cles=[],
                type_modalites_diffusion='',
                limitations_additionnelles_chapitres='',
                signataires=[],
                date_embargo=None,
                modalites_diffusion_acceptees_le=None,
            )
        )

        response = self.client.post(self.url, data={})

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.update_authorization_distribution.assert_called()
        self.mock_doctorate_api.return_value.update_authorization_distribution.assert_called_with(
            uuid=self.doctorate_uuid,
            update_authorization_distribution=UpdateAuthorizationDistribution._new_from_openapi_data(
                sources_financement='',
                resume_anglais='',
                resume_autre_langue='',
                langue_redaction_these='',
                mots_cles=[],
                type_modalites_diffusion='',
                date_embargo=None,
                limitations_additionnelles_chapitres='',
                modalites_diffusion_acceptees='',
            ),
            **self.api_default_params,
        )

    def test_post_invalid_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.return_value = (
            AuthorizationDistributionDTO._from_openapi_data(
                uuid=self.doctorate_uuid,
                statut='DIFFUSION_NON_SOUMISE',
                sources_financement='',
                resume_anglais='',
                resume_autre_langue='',
                mots_cles=[],
                type_modalites_diffusion='',
                limitations_additionnelles_chapitres='',
                signataires=[],
                date_embargo=None,
                modalites_diffusion_acceptees_le=None,
            )
        )

        response = self.client.post(
            self.url,
            data={
                'langue_redaction_these': LANGUAGE_UNDECIDED,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 1)
        self.assertIn(gettext('Please select a language.'), form.errors.get('langue_redaction_these'))

    def test_post_authorization_distribution_data_and_send_it_to_the_supervisor(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={
                'sources_financement': 'New sources',
                'resume_anglais': 'New summary in english',
                'resume_autre_langue': 'New summary in another language',
                'langue_redaction_these': 'FR',
                'mots_cles': 'word-3,word-4',
                'type_modalites_diffusion': TypeModalitesDiffusionThese.ACCES_RESTREINT.name,
                'date_embargo': datetime.date(2026, 2, 2).isoformat(),
                'limitations_additionnelles_chapitres': 'New limitations',
                'accepter_conditions': 'on',
                'doctorate-main-form-confirm-modal-button': '',
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url, fetch_redirect_response=False)

        accepted_content = render_to_string(
            'parcours_doctoral/includes/authorization_distribution/authorization_distribution_acceptation.html'
        )

        # Call the API with the right data
        self.mock_doctorate_api.return_value.update_authorization_distribution.assert_not_called()
        self.mock_doctorate_api.return_value.send_authorization_distribution_to_promoter.assert_called()
        self.mock_doctorate_api.return_value.send_authorization_distribution_to_promoter.assert_called_with(
            uuid=self.doctorate_uuid,
            send_authorization_distribution_to_promoter=SendAuthorizationDistributionToPromoter._new_from_openapi_data(
                sources_financement='New sources',
                resume_anglais='New summary in english',
                resume_autre_langue='New summary in another language',
                langue_redaction_these='FR',
                mots_cles=['word-3', 'word-4'],
                type_modalites_diffusion=TypeModalitesDiffusionThese.ACCES_RESTREINT.name,
                date_embargo=None,
                limitations_additionnelles_chapitres='New limitations',
                modalites_diffusion_acceptees=accepted_content,
            ),
            **self.api_default_params,
        )
