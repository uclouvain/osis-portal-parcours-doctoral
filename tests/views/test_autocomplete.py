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
import json
import uuid
from unittest.mock import ANY, Mock, patch

from django.urls import reverse
from osis_organisation_sdk.models.entite import Entite
from osis_organisation_sdk.models.paginated_entites import PaginatedEntites
from osis_reference_sdk.models.academic_calendar import AcademicCalendar
from osis_reference_sdk.models.scholarship import Scholarship

from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase
from parcours_doctoral.contrib.enums.scholarship import TypeBourse
from parcours_doctoral.tests.utils import MockCountry, MockLanguage

DEFAULT_API_PARAMS = {
    'accept_language': ANY,
    'x_user_first_name': ANY,
    'x_user_last_name': ANY,
    'x_user_email': ANY,
    'x_user_global_id': ANY,
}


class AutocompleteTestCase(OsisPortalTestCase):

    def setUp(self):
        self.client.force_login(PersonFactory().user)

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

    @patch('osis_parcours_doctoral_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_tutors(self, api):
        api.return_value.autocomplete_tutor_list.return_value = {
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

    @patch('osis_parcours_doctoral_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_persons(self, api):
        api.return_value.autocomplete_person_list.return_value = {
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

    @patch('osis_learning_unit_sdk.api.learning_units_api.LearningUnitsApi')
    @patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
    def test_autocomplete_learning_unit_year(self, mock_anac, api):
        today = datetime.date.today()
        mock_anac.return_value.get_academic_years.return_value = Mock(
            results=[
                AcademicCalendar(
                    year=2019,
                    start_date=today - datetime.timedelta(days=1),
                    end_date=today + datetime.timedelta(days=1),
                )
            ]
        )
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

    @patch('osis_reference_sdk.api.scholarship_api.ScholarshipApi')
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
