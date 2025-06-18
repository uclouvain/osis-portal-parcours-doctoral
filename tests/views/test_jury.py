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
from unittest.mock import Mock

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.model.action_link import ActionLink

from parcours_doctoral.contrib.enums import (
    FormuleDefense,
    GenreMembre,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.contrib.forms.jury.membre import JuryMembreForm
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class JuryPreparationTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url("parcours_doctoral:update:jury-preparation", pk=cls.doctorate_uuid)
        cls.detail_url = resolve_url("parcours_doctoral:jury-preparation", pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_jury_preparation.return_value = Mock(
            titre_propose="titre",
            formule_defense=FormuleDefense.FORMULE_1.name,
            date_indicative=datetime.date(2023, 4, 19),
            langue_redaction='FR',
            langue_soutenance='FR',
            commentaire="Foobar",
        )

    def test_jury_update_no_permission(self):
        self.mock_doctorate_object.links['update_jury_preparation'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_jury_get_no_permission(self):
        self.mock_doctorate_object.links['retrieve_jury_preparation'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

    def test_jury_get(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Foobar")

    def test_jury_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Foobar")
        self.assertContains(response, '<form')
        self.assertEqual(response.context['form'].initial['titre_propose'], "titre")

    def test_jury_update_with_data(self):
        response = self.client.post(
            self.url,
            {
                "titre_propose": "titre bis",
                "formule_defense": FormuleDefense.FORMULE_1.name,
                "date_indicative": '2023-04-01',
                "langue_redaction": 'FR',
                "langue_soutenance": 'FR',
                "commentaire": "Foobar bis",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.update_jury_preparation.assert_called()
        last_call_kwargs = self.mock_doctorate_api.return_value.update_jury_preparation.call_args[1]
        self.assertIn("titre_propose", last_call_kwargs['modifier_jury_command'])
        self.assertEqual(last_call_kwargs['modifier_jury_command']['titre_propose'], "titre bis")


class JuryTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.detail_url = resolve_url("parcours_doctoral:jury", pk=self.doctorate_uuid)
        self.form_url = resolve_url("parcours_doctoral:update:jury", pk=self.doctorate_uuid)

        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_jury_preparation.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.mock_doctorate_api.return_value.list_jury_members.return_value = [
            Mock(
                uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
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
            ),
            Mock(
                uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                role=RoleJury.SECRETAIRE.name,
                est_promoteur=True,
                matricule='0123456',
                institution='UCLouvain',
                autre_institution='',
                pays='pays',
                nom='autre nom',
                prenom='autre prenom',
                titre=TitreMembre.DOCTEUR.name,
                justification_non_docteur='',
                genre=GenreMembre.AUTRE.name,
                email='email',
            ),
        ]

    def test_jury_get_no_permission(self):
        self.mock_doctorate_object.links['list_jury_members'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

    def test_jury_get(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, "autre nom")

    def test_jury_create_no_permission(self):
        self.mock_doctorate_object.links['create_jury_members'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, 403)

    def test_jury_create(self):
        response = self.client.get(self.form_url)
        self.assertContains(response, "autre nom")

    def test_jury_create_with_data(self, *args):
        response = self.client.post(
            self.form_url,
            {
                "institution_principale": JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                "matricule": '',
                "institution": 'Université autre',
                "autre_institution": '',
                "pays": 'pays',
                "nom": 'nom',
                "prenom": 'prenom',
                "titre": TitreMembre.DOCTEUR.name,
                "justification_non_docteur": '',
                "genre": GenreMembre.AUTRE.name,
                "email": 'email@example.org',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.create_jury_members.assert_called()
        last_call_kwargs = self.mock_doctorate_api.return_value.create_jury_members.call_args[1]
        self.assertIn("matricule", last_call_kwargs['ajouter_membre_command'])
        self.assertEqual(last_call_kwargs['ajouter_membre_command']['email'], "email@example.org")
