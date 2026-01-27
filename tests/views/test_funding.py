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
from uuid import uuid4

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.models.action_link import ActionLink

from admission.constants import FIELD_REQUIRED_MESSAGE
from frontoffice.settings.osis_sdk.utils import (
    ApiBusinessException,
    MultipleApiBusinessException,
)
from parcours_doctoral.contrib.enums import AdmissionType
from parcours_doctoral.contrib.enums.financement import (
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from parcours_doctoral.services.doctorate import ParcoursDoctoralBusinessException
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class FundingDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:funding', pk=cls.doctorate_uuid)

    def test_detail_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links.retrieve_funding = ActionLink(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_detail(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertContains(response, ChoixTypeFinancement.WORK_CONTRACT.value)
        self.assertContains(response, ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.value)


class FundingFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.default_data = {
            'type': '',
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            'eft': 10,
            'bourse_recherche': cls.scholarship_uuid,
            'autre_bourse_recherche': 'Other scholarship',
            'bourse_date_debut': datetime.date(2020, 2, 2),
            'bourse_date_fin': datetime.date(2024, 2, 2),
            'bourse_preuve_0': str(uuid4()),
            'duree_prevue': 10,
            'temps_consacre': 20,
            'est_lie_fnrs_fria_fresh_csc': True,
            'commentaire': 'Comment',
        }

        cls.url = resolve_url('parcours_doctoral:update:funding', pk=cls.doctorate_uuid)

    def test_update_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links.update_funding = ActionLink(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_form_initialization(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<form ')

        form = response.context['form']

        self.assertCountEqual(
            form.fields['bourse_recherche'].widget.choices,
            [
                ('', ' - '),
                (self.scholarship_uuid, 'Doctorate Scholarship 1'),
            ],
        )

        # The scholarship has no long name -> the short name is displayed
        self.mock_scholarship_object.long_name = ''

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertCountEqual(
            form.fields['bourse_recherche'].widget.choices,
            [
                ('', ' - '),
                (self.scholarship_uuid, 'DS1'),
            ],
        )

        # The doctorate has no scholarship
        self.mock_doctorate_object.financement.bourse_recherche = None

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertCountEqual(
            form.fields['bourse_recherche'].widget.choices,
            [],
        )

    def test_form_initialization_for_an_admission(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.ADMISSION.name

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        for field in [
            'type',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'est_lie_fnrs_fria_fresh_csc',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'commentaire',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

    def test_form_initialization_for_a_pre_admission(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.PRE_ADMISSION.name

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        for field in [
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'commentaire',
            'type',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'est_lie_fnrs_fria_fresh_csc',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

    def test_post_invalid_form_for_an_admission_without_data(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.ADMISSION.name

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 4)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))

    def test_post_invalid_form_for_an_admission_and_a_work_contract(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.ADMISSION.name

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 5)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type_contrat_travail', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('eft', []))

    def test_post_invalid_form_for_an_admission_and_a_scholarship(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.ADMISSION.name

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 8)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_recherche', []))
        self.assertIn('', form.errors.get('autre_bourse_recherche', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_date_debut', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_date_fin', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_preuve', []))

    def test_post_invalid_form_for_an_admission_and_a_self_funding(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 3)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))

    def test_post_invalid_form_for_a_pre_admission_and_a_work_contract(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.PRE_ADMISSION.name

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 2)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type_contrat_travail', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('eft', []))

        self.mock_doctorate_api.return_value.update_funding.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(
                    status_code=ParcoursDoctoralBusinessException.ContratTravailInconsistantException.value,
                    detail='Custom error',
                ),
            }
        )

        response = self.client.post(
            self.url,
            data={
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
                'type_contrat_travail': 'Custom error',
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertIn('Custom error', form.errors.get('type_contrat_travail', []))

    def test_post_invalid_form_for_a_pre_admission_and_a_scholarship(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.type_admission = AdmissionType.PRE_ADMISSION.name

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 2)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_recherche', []))
        self.assertIn('', form.errors.get('autre_bourse_recherche', []))

    def test_valid_update_for_self_funding(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.mock_doctorate_api.return_value.update_funding.assert_called_once_with(
            uuid=self.doctorate_uuid,
            modifier_financement_command={
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
                'type_contrat_travail': '',
                'eft': None,
                'bourse_recherche': '',
                'autre_bourse_recherche': '',
                'bourse_date_debut': None,
                'bourse_date_fin': None,
                'bourse_preuve': [],
                'duree_prevue': self.default_data['duree_prevue'],
                'temps_consacre': self.default_data['temps_consacre'],
                'est_lie_fnrs_fria_fresh_csc': self.default_data['est_lie_fnrs_fria_fresh_csc'],
                'commentaire': self.default_data['commentaire'],
            },
            **self.api_default_params,
        )

    def test_valid_update_for_work_contract(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.mock_doctorate_api.return_value.update_funding.assert_called_with(
            uuid=self.doctorate_uuid,
            modifier_financement_command={
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
                'type_contrat_travail': self.default_data['type_contrat_travail'],
                'eft': self.default_data['eft'],
                'bourse_recherche': '',
                'autre_bourse_recherche': '',
                'bourse_date_debut': None,
                'bourse_date_fin': None,
                'bourse_preuve': [],
                'duree_prevue': self.default_data['duree_prevue'],
                'temps_consacre': self.default_data['temps_consacre'],
                'est_lie_fnrs_fria_fresh_csc': self.default_data['est_lie_fnrs_fria_fresh_csc'],
                'commentaire': self.default_data['commentaire'],
            },
            **self.api_default_params,
        )

    def test_valid_update_for_search_scholarship(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.mock_doctorate_api.return_value.update_funding.assert_called_with(
            uuid=self.doctorate_uuid,
            modifier_financement_command={
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                'type_contrat_travail': '',
                'eft': None,
                'bourse_recherche': self.default_data['bourse_recherche'],
                'autre_bourse_recherche': '',
                'bourse_date_debut': self.default_data['bourse_date_debut'],
                'bourse_date_fin': self.default_data['bourse_date_fin'],
                'bourse_preuve': [self.default_data['bourse_preuve_0']],
                'duree_prevue': self.default_data['duree_prevue'],
                'temps_consacre': self.default_data['temps_consacre'],
                'est_lie_fnrs_fria_fresh_csc': self.default_data['est_lie_fnrs_fria_fresh_csc'],
                'commentaire': self.default_data['commentaire'],
            },
            **self.api_default_params,
        )
        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                'bourse_recherche': '',
            },
        )
        self.assertEqual(response.status_code, 302)

        self.mock_doctorate_api.return_value.update_funding.assert_called_with(
            uuid=self.doctorate_uuid,
            modifier_financement_command={
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                'type_contrat_travail': '',
                'eft': None,
                'bourse_recherche': '',
                'autre_bourse_recherche': self.default_data['autre_bourse_recherche'],
                'bourse_date_debut': self.default_data['bourse_date_debut'],
                'bourse_date_fin': self.default_data['bourse_date_fin'],
                'bourse_preuve': [self.default_data['bourse_preuve_0']],
                'duree_prevue': self.default_data['duree_prevue'],
                'temps_consacre': self.default_data['temps_consacre'],
                'est_lie_fnrs_fria_fresh_csc': self.default_data['est_lie_fnrs_fria_fresh_csc'],
                'commentaire': self.default_data['commentaire'],
            },
            **self.api_default_params,
        )
