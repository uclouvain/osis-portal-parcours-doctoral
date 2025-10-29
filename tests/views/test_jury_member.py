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
from unittest import mock
from unittest.mock import ANY, Mock

from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from mock import patch

from frontoffice.settings.osis_sdk.utils import (
    ApiBusinessException,
    MultipleApiBusinessException,
)
from osis_parcours_doctoral_sdk.model.approuver_jury_command import ApprouverJuryCommand
from osis_parcours_doctoral_sdk.model.refuser_jury_command import RefuserJuryCommand
from osis_reference_sdk.model.country import Country
from parcours_doctoral.contrib.enums import (
    DecisionApprovalEnum,
    GenreMembre,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.contrib.forms import PDF_MIME_TYPE
from parcours_doctoral.contrib.forms.jury.membre import JuryMembreForm
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class JuryMembreUpdateTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.country = Country(name='CountryName')

    def setUp(self):
        super().setUp()

        self.url = resolve_url(
            "parcours_doctoral:update:jury-member:update",
            pk=self.doctorate_uuid,
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )

        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid="123cdc60-2537-4a12-a396-64d2e9e34876",
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays=self.country.name,
            nom='nom-detail',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )
        api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

    def test_jury_membre_change_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "nom-detail")
        self.assertContains(response, '<form')
        self.assertEqual(response.context['form'].initial['nom'], "nom-detail")

    def test_jury_membre_change_post_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "institution_principale": JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                "matricule": '',
                "institution": 'Université autre',
                "autre_institution": '',
                "pays": self.country.name,
                "nom": 'nom-nouveau',
                "prenom": 'prenom',
                "titre": TitreMembre.DOCTEUR.name,
                "justification_non_docteur": '',
                "genre": GenreMembre.AUTRE.name,
                "email": 'email@example.org',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.update_jury_member.assert_called()
        last_call_kwargs = self.mock_doctorate_api.return_value.update_jury_member.call_args[1]
        self.assertIn("nom", last_call_kwargs['modifier_membre_command'])
        self.assertEqual(last_call_kwargs['modifier_membre_command']['nom'], "nom-nouveau")


class JuryMemberRemoveTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.url = resolve_url(
            "parcours_doctoral:update:jury-member:remove",
            pk=self.doctorate_uuid,
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid=self.doctorate_uuid,
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays='pays',
            nom='nom',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

    def test_jury_remove_post(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.remove_jury_member.assert_called()


class JuryMemberChangeRoleTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.url = resolve_url(
            "parcours_doctoral:update:jury-member:change-role",
            pk=self.doctorate_uuid,
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid=self.doctorate_uuid,
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays='pays',
            nom='nom',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

    def test_jury_create_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "role": RoleJury.PRESIDENT.name,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.update_role_jury_member.assert_called()
        last_call_kwargs = self.mock_doctorate_api.return_value.update_role_jury_member.call_args[1]
        self.assertIn("role", last_call_kwargs['patched_modifier_role_membre_command'])
        self.assertEqual(last_call_kwargs['patched_modifier_role_membre_command']['role'], RoleJury.PRESIDENT.name)


class JuryMemberApprovalTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.detail_url = resolve_url(
            "parcours_doctoral:jury",
            pk=self.doctorate_uuid,
        )
        self.client.force_login(self.person.user)
        self.mock_doctorate_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid=self.doctorate_uuid,
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays='pays',
            nom='nom',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

        self.external_api_token_header = {'Token': 'api-token-external'}
        self.detail_url = resolve_url("parcours_doctoral:jury", pk=self.doctorate_uuid)
        self.external_url = resolve_url(
            "parcours_doctoral:jury-external-approval",
            pk=self.doctorate_uuid,
            token="promoter-token",
        )
        self.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }
        self.external_kwargs = {
            'accept_language': ANY,
            'token': 'promoter-token',
        }

    @mock.patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, 'size': 1},
    )
    def test_should_approval_by_pdf_redirect_without_errors(self, *args):
        url = resolve_url("parcours_doctoral:approve-by-pdf", pk=self.doctorate_uuid)
        response = self.client.post(url, {'matricule': "test", 'pdf_0': 'some_file'})
        expected_url = resolve_url("parcours_doctoral:jury", pk=self.doctorate_uuid)
        self.assertRedirects(response, expected_url)

    def test_should_approval_by_pdf_redirect_with_errors(self):
        url = resolve_url("parcours_doctoral:approve-by-pdf", pk=self.doctorate_uuid)
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url)

    def test_should_resend_invite(self):
        url = resolve_url(
            "parcours_doctoral:resend-invite",
            pk=self.doctorate_uuid,
            uuid="uuid-9876543210",
        )

        with self.subTest('OK'):
            response = self.client.post(url, {}, follow=True)
            self.assertRedirects(response, self.detail_url)
            self.assertContains(response, _("An invitation has been sent again."))
            self.assertTrue(self.mock_doctorate_api.return_value.resend_invite.called)

        with self.subTest('KO'):
            self.mock_doctorate_api.return_value.resend_invite.side_effect = MultipleApiBusinessException(
                exceptions={ApiBusinessException(42, "Something went wrong")}
            )
            response = self.client.post(url, {}, follow=True)
            self.assertRedirects(response, self.detail_url)
            self.assertNotContains(response, _("An invitation has been sent again."))

    def test_should_external_promoter_access_info(self):
        self.client.logout()
        response = self.client.get(self.external_url)
        self.assertTemplateUsed(response, 'parcours_doctoral/forms/jury/external_approval.html' "")
        self.assertEqual(self.mock_doctorate_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_doctorate_api.return_value.get_external_jury.assert_called()

    def test_should_external_promoter_approve_jury(self):
        self.client.logout()
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_doctorate_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_doctorate_api.return_value.approve_external_jury.assert_called_with(
            uuid=self.doctorate_uuid,
            approuver_jury_command=ApprouverJuryCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'uuid_membre': "promoter-token",
                }
            ),
            **self.external_kwargs,
        )

    def test_should_external_promoter_reject_jury(self):
        self.client.logout()
        # All data is provided and the jury is rejected
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_doctorate_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_doctorate_api.return_value.reject_external_jury.assert_called_with(
            uuid=self.doctorate_uuid,
            refuser_jury_command=RefuserJuryCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'motif_refus': "The reason",
                    'uuid_membre': "promoter-token",
                }
            ),
            **self.external_kwargs,
        )

    def test_should_external_promoter_error_with_no_decision(self):
        self.client.logout()
        # The decision is missing
        response = self.client.post(
            self.external_url,
            {
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('decision', response.context['approval_form'].errors)

        self.mock_doctorate_api.return_value.reject_jury.assert_not_called()
        self.mock_doctorate_api.return_value.approve_jury.assert_not_called()

    def test_should_external_promoter_reject_with_error_when_no_motive(self):
        self.client.logout()
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('motif_refus', response.context['approval_form'].errors)

        self.mock_doctorate_api.return_value.reject_jury.assert_not_called()
        self.mock_doctorate_api.return_value.approve_jury.assert_not_called()

    def test_should_approve_jury(self):
        # All data is provided and the jury is approved
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",  # The reason is provided but will not be used
            },
        )

        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.approve_jury.assert_called_with(
            uuid=self.doctorate_uuid,
            approuver_jury_command=ApprouverJuryCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'uuid_membre': "74ca8fbf-4566-437c-b6bb-c0c4780ec046",
                }
            ),
            **self.default_kwargs,
        )

    def test_should_reject_jury(self):
        # All data is provided and the jury is rejected
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.mock_doctorate_api.return_value.reject_jury.assert_called_with(
            uuid=self.doctorate_uuid,
            refuser_jury_command=RefuserJuryCommand(
                **{
                    'commentaire_externe': "The public comment",
                    'commentaire_interne': "The internal comment",
                    'motif_refus': "The reason",
                    'uuid_membre': "74ca8fbf-4566-437c-b6bb-c0c4780ec046",
                }
            ),
            **self.default_kwargs,
        )

    def test_should_error_with_no_decision(self):
        # The decision is missing
        response = self.client.post(
            self.detail_url,
            {
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('decision', response.context['approval_form'].errors)

        self.mock_doctorate_api.return_value.reject_jury.assert_not_called()
        self.mock_doctorate_api.return_value.approve_jury.assert_not_called()
