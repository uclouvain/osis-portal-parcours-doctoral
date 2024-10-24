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
import uuid
from unittest.mock import patch, MagicMock

from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto_cotutelle import ParcoursDoctoralDTOCotutelle

from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class BaseCotutelleTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        superior_institute_patcher = patch('osis_reference_sdk.api.universities_api.UniversitiesApi')
        self.mock_superior_institute_api = superior_institute_patcher.start()

        self.mock_superior_institute_api.return_value.university_read.return_value = MagicMock(
            uuid='foo',
            name='foo',
            street='foo',
            street_number='foo',
            zipcode='foo',
            city='foo',
        )
        self.addCleanup(superior_institute_patcher.stop)


class CotutelleDetailViewTestCase(BaseCotutelleTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:cotutelle', pk=cls.doctorate_uuid)

    def test_get_cotutelle_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_cotutelle'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_cotutelle_get(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertContains(response, 'Cotutelle reason')


class CotutelleFormViewTestCase(BaseCotutelleTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:update:cotutelle', pk=cls.doctorate_uuid)

    def test_update_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_cotutelle'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_cotutelle_get_form(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertContains(response, 'dependsOn.min.js', count=1)
        self.assertContains(response, 'Cotutelle reason')
        self.assertContains(response, '<form')
        self.assertEqual(response.context['form'].initial['cotutelle'], 'YES')

    def test_cotutelle_get_form_no_cotutelle(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.cotutelle = ParcoursDoctoralDTOCotutelle._from_openapi_data(
            cotutelle=False,
            motivation='',
            institution='',
            institution_fwb=None,
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
            autre_institution_nom='',
            autre_institution_adresse='',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.context['form'].initial['cotutelle'], 'NO')

    def test_cotutelle_update_with_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            {
                'cotutelle': 'YES',
                'motivation': 'Barbaz',
                'institution': 'Bazbar',
                'institution_fwb': False,
                'demande_ouverture_0': str(uuid.uuid4()),
                'convention': [],
                'autres_documents': [],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_doctorate_api.return_value.update_cotutelle.assert_called()
        last_call_kwargs = self.mock_doctorate_api.return_value.update_cotutelle.call_args[1]
        self.assertIn('motivation', last_call_kwargs['modifier_cotutelle_command'])
        self.assertEqual(last_call_kwargs['modifier_cotutelle_command']['motivation'], 'Barbaz')

    def test_cotutelle_update_without_data(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, {'cotutelle': 'NO', 'motivation': 'Barbaz'})
        self.assertEqual(response.status_code, 302)
        last_call_kwargs = self.mock_doctorate_api.return_value.update_cotutelle.call_args[1]
        self.assertEqual(last_call_kwargs['modifier_cotutelle_command']['motivation'], '')

    def test_cotutelle_update_missing_data(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, {'cotutelle': 'YES', 'motivation': 'Barbaz'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'institution', _('This field is required.'))
