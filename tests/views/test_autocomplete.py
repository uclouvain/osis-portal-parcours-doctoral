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

import json
import uuid
from unittest.mock import ANY, Mock, patch

from django.test import TestCase
from django.urls import reverse
from osis_organisation_sdk.model.address import Address
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites

from base.tests.factories.person import PersonFactory
from osis_admission_sdk.model.doctorat_dto import DoctoratDTO
from osis_admission_sdk.model.scholarship import Scholarship
from parcours_doctoral.contrib.enums.scholarship import TypeBourse
from parcours_doctoral.tests.utils import MockCity, MockCountry, MockLanguage

DEFAULT_API_PARAMS = {
    'accept_language': ANY,
    'x_user_first_name': ANY,
    'x_user_last_name': ANY,
    'x_user_email': ANY,
    'x_user_global_id': ANY,
}


class AutocompleteTestCase(TestCase):
    def setUp(self):
        self.client.force_login(PersonFactory().user)

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_doctorate(self, api):
        api.return_value.list_doctorat_dtos.return_value = [
            DoctoratDTO(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                sigle_entite_gestion="CDE",
                campus="Louvain-La-Neuve",
                type='PHD',
                campus_inscription='Mons',
                code='CODE',
            ),
        ]
        url = reverse('parcours_doctoral:autocomplete:doctorate')
        response = self.client.get(url, {'forward': json.dumps({'sector': 'SSH'}), 'q': 'foo'})
        results = [
            {
                'id': 'FOOBAR-2021',
                'sigle': 'FOOBAR',
                'sigle_entite_gestion': 'CDE',
                'text': 'Foobar (Louvain-La-Neuve) <span class="training-acronym">FOOBAR</span>',
            }
        ]
        self.assertDictEqual(response.json(), {'results': results})
        api.return_value.list_doctorat_dtos.assert_called_with(
            acronym_or_name='foo',
            sigle='SSH',
            campus='',
            **DEFAULT_API_PARAMS,
        )

    @patch('osis_reference_sdk.api.countries_api.CountriesApi')
    def test_autocomplete_country(self, api):
        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True),
            ]
        )
        url = reverse('parcours_doctoral:autocomplete:country')
        response = self.client.get(url, {'q': ''})
        expected = [
            {
                'id': 'BE',
                'text': 'Belgique',
                'european_union': True,
            },
            {
                'id': None,
                'text': '<hr>',
            },
            {
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            },
            {
                'id': 'BE',
                'text': 'Belgique',
                'european_union': True,
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected, 'pagination': {'more': False}})
        api.return_value.countries_list.assert_called()

        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
            ]
        )
        response = self.client.get(url, {'q': 'F'})
        expected = [
            {
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            }
        ]
        self.assertDictEqual(response.json(), {'results': expected, 'pagination': {'more': False}})
        self.assertEqual(api.return_value.countries_list.call_args[1]['search'], 'F')

        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
            ]
            * 20
        )
        url = reverse('parcours_doctoral:autocomplete:country')
        response = self.client.get(url)
        results = response.json()
        self.assertEqual(len(results['results']), 22)
        self.assertIs(results['pagination']['more'], True)
        api.return_value.countries_list.assert_called()

    @patch('osis_reference_sdk.api.languages_api.LanguagesApi')
    def test_autocomplete_languages(self, api):
        api.return_value.languages_list.return_value = Mock(
            results=[
                MockLanguage(code='FR', name='Français', name_en='French'),
                MockLanguage(code='EN', name='Anglais', name_en='English'),
            ]
        )
        url = reverse('parcours_doctoral:autocomplete:language')
        response = self.client.get(url, {'q': ''})
        expected = [
            {
                'id': 'FR',
                'text': 'Français',
            },
            {
                'id': 'EN',
                'text': 'Anglais',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})
        api.return_value.languages_list.assert_called()

        api.return_value.languages_list.return_value = Mock(
            results=[
                MockLanguage(code='FR', name='Français', name_en='French'),
            ]
        )
        response = self.client.get(url, {'q': 'F'})
        expected = [
            {
                'id': 'FR',
                'text': 'Français',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})
        self.assertEqual(api.return_value.languages_list.call_args[1]['search'], 'F')

    @patch('osis_reference_sdk.api.cities_api.CitiesApi')
    def test_autocomplete_city(self, api):
        api.return_value.cities_list.return_value = Mock(
            results=[
                MockCity(name='Pintintin-les-Creumeuil'),
                MockCity(name='Montreuil-les-Sardouille'),
            ]
        )
        url = reverse('parcours_doctoral:autocomplete:city')
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': ''})
        expected = [
            {
                'id': 'Pintintin-les-Creumeuil',
                'text': 'Pintintin-les-Creumeuil',
            },
            {
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')

        api.return_value.cities_list.return_value = Mock(
            results=[
                MockCity(name='Montreuil-les-Sardouille'),
            ]
        )
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': 'Mont'})
        expected = [
            {
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

        # Without the postal code
        response = self.client.get(url, {'forward': json.dumps({'postal_code': ''}), 'q': 'Mont'})
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_tutors(self, api):
        api.return_value.list_tutors.return_value = {
            'results': [
                Mock(first_name='Michel', last_name='Screugnette', global_id="0123456987"),
                Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
            ]
        }
        url = reverse('parcours_doctoral:autocomplete:tutor')
        response = self.client.get(url, {'q': 'm'})
        expected = [
            {
                'id': '0123456987',
                'text': 'Michel Screugnette',
            },
            {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_persons(self, api):
        api.return_value.list_people.return_value = {
            'results': [
                Mock(first_name='Ripolin', last_name='Trolapois', global_id="0123456987"),
                Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
            ]
        }
        url = reverse('parcours_doctoral:autocomplete:person')
        response = self.client.get(url, {'q': 'm'})
        expected = [
            {
                'id': '0123456987',
                'text': 'Ripolin Trolapois',
            },
            {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_organisation_sdk.api.entites_api.EntitesApi')
    def test_autocomplete_institute_list(self, api):
        mock_entities = [
            Entite(
                uuid='uuid1',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of technology',
                acronym='IT',
            ),
            Entite(
                uuid='uuid2',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of foreign languages',
                acronym='IFL',
            ),
        ]
        api.return_value.get_entities.return_value = PaginatedEntites(
            results=mock_entities,
        )
        url = reverse('parcours_doctoral:autocomplete:institute')
        response = self.client.get(url, {'q': 'Institute'})
        expected = [
            {
                'id': 'uuid1',
                'text': 'Institute of technology (IT)',
            },
            {
                'id': 'uuid2',
                'text': 'Institute of foreign languages (IFL)',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_organisation_sdk.api.entites_api.EntitesApi')
    def test_autocomplete_institute_location(self, api):
        mock_locations = [
            Address(
                state='Belgique',
                street='Place de l\'université',
                street_number='1',
                postal_code='1348',
                city='Ottignies-Louvain-la-Neuve',
                country_iso_code='BE',
                is_main=True,
            ),
            Address(
                state='Belgique',
                street='Avenue E. Mounier',
                street_number='81',
                postal_code='1200',
                city='Woluwe-Saint-Lambert',
                country_iso_code='BE',
                is_main=True,
            ),
        ]
        # TODO This will become (again) paginated later
        # api.return_value.get_entity_addresses.return_value = PaginatedAddresses(
        #     results=mock_locations,
        #     next=None,
        # )
        api.return_value.get_entity_addresses.return_value = mock_locations[0]
        url = reverse('parcours_doctoral:autocomplete:institute-location')

        response = self.client.get(url, {'forward': json.dumps({'institut_these': ''})}, {'uuid': 'uuid1'})
        self.assertDictEqual(response.json(), {'results': []})

        response = self.client.get(url, {'forward': json.dumps({'institut_these': 'IFL'})}, {'uuid': 'uuid1'})
        expected = [
            {
                'id': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                'text': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                # }, {
                #     'id': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
                #     'text': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})

    @patch('osis_learning_unit_sdk.api.learning_units_api.LearningUnitsApi')
    def test_autocomplete_learning_unit_year(self, api):
        api.return_value.learningunits_list.return_value = {
            'results': [
                dict(acronym="ESA2004", title="dumb text"),
                dict(acronym="ESA2006", title="dumb text 2"),
            ]
        }
        url = reverse('parcours_doctoral:autocomplete:learning-unit-years')
        response = self.client.get(url, {'q': 'ES', 'forward': json.dumps({'academic_year': '2021'})})
        expected = [
            {'id': "ESA2004", 'text': "ESA2004 - dumb text"},
            {'id': "ESA2006", 'text': "ESA2006 - dumb text 2"},
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_scholarship(self, api):
        first_scholarship_uuid = str(uuid.uuid4())
        second_scholarship_uuid = str(uuid.uuid4())

        mock_scholarships = [
            Scholarship._from_openapi_data(
                uuid=first_scholarship_uuid,
                short_name="EM-1",
                long_name="Erasmus Mundus 1",
                type=TypeBourse.ERASMUS_MUNDUS.name,
            ),
            Scholarship._from_openapi_data(
                uuid=second_scholarship_uuid,
                short_name="EM-2",
                long_name="",
                type=TypeBourse.ERASMUS_MUNDUS.name,
            ),
        ]

        api.return_value.list_scholarships.return_value = {
            'results': mock_scholarships,
        }
        url = reverse('parcours_doctoral:autocomplete:scholarship')

        response = self.client.get(
            url, {'q': 'Erasmus', 'forward': json.dumps({'type': TypeBourse.ERASMUS_MUNDUS.name})}
        )
        expected = [
            {'id': first_scholarship_uuid, 'text': "Erasmus Mundus 1"},
            {'id': second_scholarship_uuid, 'text': "EM-2"},
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})