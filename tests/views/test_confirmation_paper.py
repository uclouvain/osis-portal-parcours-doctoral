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
import datetime
from unittest.mock import Mock

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.models.action_link import ActionLink

from base.tests.factories.person import PersonFactory
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class ConfirmationPaperDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:confirmation-paper', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_confirmation_papers.return_value = [
            Mock(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
            Mock(
                uuid='c2',
                date_limite='2022-05-10',
                date='2022-04-02',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
            Mock(
                uuid='c3',
                date_limite='2022-04-10',
                date='2022-04-01',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
        ]

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_confirmation'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_several_confirmation_papers(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_confirmation_papers.assert_called()

        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertIsNotNone(response.context.get('current_confirmation_paper'))
        self.assertEqual(response.context.get('current_confirmation_paper').uuid, 'c1')

        self.assertEqual(len(response.context.get('previous_confirmation_papers')), 2)
        self.assertEqual(response.context.get('previous_confirmation_papers')[0].uuid, 'c2')
        self.assertEqual(response.context.get('previous_confirmation_papers')[1].uuid, 'c3')

    def test_get_no_confirmation_paper(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_confirmation_papers.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_confirmation_papers.assert_called()

        self.assertIsNone(response.context.get('current_confirmation_paper'))

        self.assertEqual(len(response.context.get('previous_confirmation_papers')), 0)


class ConfirmationPaperFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.promoter = PersonFactory()
        cls.url = resolve_url('parcours_doctoral:update:confirmation-paper', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = Mock(
            uuid='c1',
            date_limite='2022-06-10',
            date='2022-04-03',
            rapport_recherche=['f1'],
            avis_renouvellement_mandat_recherche=['f2'],
            proces_verbal_ca=['f3'],
            to_dict=dict(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=['f1'],
                avis_renouvellement_mandat_recherche=['f2'],
                proces_verbal_ca=['f3'],
            ),
        )

    def test_get_no_permission_with_student(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['update_confirmation'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_no_permission_with_promoter(self):
        self.client.force_login(self.promoter.user)
        self.mock_doctorate_object.links['upload_pdf_confirmation'] = ActionLink._from_openapi_data(
            error='access error'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_several_confirmation_papers_with_a_person(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, 'c1')

        # Initialize the form
        self.assertEqual(response.context.get('form').initial['date'], '2022-04-03')
        self.assertEqual(response.context.get('form').initial['rapport_recherche'], ['f1'])
        self.assertEqual(response.context.get('form').initial['avis_renouvellement_mandat_recherche'], ['f2'])
        self.assertEqual(response.context.get('form').initial['proces_verbal_ca'], ['f3'])

    def test_get_no_confirmation_paper_with_a_person(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = None

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('form').initial, {})

    def test_post_a_confirmation_paper_with_a_person(self):
        self.client.force_login(self.person.user)

        self.client.post(
            self.url,
            data={
                'date': datetime.date(2022, 4, 4),
                'rapport_recherche_0': ['f11'],
                'avis_renouvellement_mandat_recherche_0': ['f22'],
                'proces_verbal_ca_0': ['f33'],
            },
        )
        # Call the API with the right data
        self.mock_doctorate_api.return_value.submit_confirmation_paper.assert_called()
        self.mock_doctorate_api.return_value.submit_confirmation_paper.assert_called_with(
            uuid=self.doctorate_uuid,
            submit_confirmation_paper_command={
                'date': datetime.date(2022, 4, 4),
                'rapport_recherche': ['f11'],
                'avis_renouvellement_mandat_recherche': ['f22'],
                'proces_verbal_ca': ['f33'],
            },
            **self.api_default_params,
        )

    def test_get_several_confirmation_papers_with_another_user(self):
        self.client.force_login(self.promoter.user)

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, 'c1')

        # Initialize the form
        self.assertEqual(response.context.get('form').initial['avis_renouvellement_mandat_recherche'], ['f2'])
        self.assertEqual(response.context.get('form').initial['proces_verbal_ca'], ['f3'])

    def test_get_no_confirmation_paper_with_another_user(self):
        self.client.force_login(self.promoter.user)

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = None

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the confirmation papers information
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('form').initial, {})

    def test_post_a_confirmation_paper_with_another_user(self):
        self.client.force_login(self.promoter.user)

        self.client.post(
            self.url,
            data={
                'avis_renouvellement_mandat_recherche_0': ['f22'],
                'proces_verbal_ca_0': ['f33'],
            },
        )
        # Call the API with the right data
        self.mock_doctorate_api.return_value.complete_confirmation_paper_by_promoter.assert_called()
        self.mock_doctorate_api.return_value.complete_confirmation_paper_by_promoter.assert_called_with(
            uuid=self.doctorate_uuid,
            complete_confirmation_paper_by_promoter_command={
                'avis_renouvellement_mandat_recherche': ['f22'],
                'proces_verbal_ca': ['f33'],
            },
            **self.api_default_params,
        )


class DoctorateConfirmationPaperCanvasExportViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:confirmation-paper-canvas', pk=cls.doctorate_uuid)

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper.return_value = Mock(
            uuid='c1',
            date_limite='2022-06-10',
            date='2022-04-03',
            rapport_recherche=['f1'],
            avis_renouvellement_mandat_recherche=['f2'],
            proces_verbal_ca=['f3'],
            to_dict=dict(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=['f1'],
                avis_renouvellement_mandat_recherche=['f2'],
                proces_verbal_ca=['f3'],
            ),
        )
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper_canvas.return_value = Mock(
            uuid='9a9adc60-2537-4a12-a396-64d2e9e34879',
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_confirmation'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_redirection_to_canvas_file_url_with_a_person(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper_canvas.assert_called()
        self.mock_doctorate_api.return_value.retrieve_last_confirmation_paper_canvas.assert_called_with(
            uuid=self.doctorate_uuid,
            **self.api_default_params,
        )

        # Check the redirection
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://dummyurl.com/document/file/foobar')
