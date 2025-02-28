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
from unittest.mock import MagicMock, Mock, patch

from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from osis_parcours_doctoral_sdk import ApiException
from osis_parcours_doctoral_sdk.model.categorie_activite import (
    CategorieActivite as CategorieActiviteModel,
)
from osis_parcours_doctoral_sdk.model.choix_type_epreuve import (
    ChoixTypeEpreuve as ChoixTypeEpreuveModel,
)
from osis_parcours_doctoral_sdk.model.contexte_formation import (
    ContexteFormation as ContexteFormationModel,
)
from osis_parcours_doctoral_sdk.model.paper import Paper
from osis_parcours_doctoral_sdk.model.seminar_communication import SeminarCommunication

from parcours_doctoral.contrib.enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    ContexteFormation,
)
from parcours_doctoral.contrib.enums.training import StatutActivite
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class TrainingTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.client.force_login(self.person.user)
        self.url = resolve_url("parcours_doctoral:doctoral-training", pk=self.doctorate_uuid)

        self.mock_doctorate_api.return_value.list_doctoral_training.return_value = []
        self.mock_doctorate_api.return_value.create_doctoral_training.return_value = dict(
            uuid='uuid-created',
        )
        self.mock_doctorate_api.return_value.update_training.return_value = dict(
            uuid='uuid-edited',
        )

        self.mock_doctorate_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.CONFERENCE.name,
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.CONFERENCE.name,
            type="",
            participating_proof=[],
            parent=None,
        )

    def test_doctoral_training_list(self):
        # This is mostly for testing {% training_categories %}
        self.mock_doctorate_api.return_value.list_doctoral_training.return_value = [
            Mock(
                spec=SeminarCommunication,
                category="COMMUNICATION",
                status=StatutActivite.NON_SOUMISE.name,
                uuid="ac5cdc60-2537-4a12-a396-64d2e9e34876",
            ),
            Mock(
                category="COMMUNICATION",
                status=StatutActivite.NON_SOUMISE.name,
                uuid="4c5cdc60-2537-4a12-a396-64d2e9e34876",
                ects=0,
            ),
            Mock(
                category="COMMUNICATION",
                status=StatutActivite.SOUMISE.name,
                uuid="5c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Communication",
                ects=5,
            ),
            Mock(
                category="CONFERENCE",
                status=StatutActivite.ACCEPTEE.name,
                uuid="6c5cdc60-2537-4a12-a396-64d2e9e34876",
                ects=5,
            ),
            Mock(
                category="PUBLICATION",
                status=StatutActivite.SOUMISE.name,
                uuid="7c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Publication",
                ects=5,
            ),
            Mock(
                category="VAE",
                status=StatutActivite.SOUMISE.name,
                uuid="8c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Valorisation",
                ects=2,
            ),
            Mock(
                category="UCL_COURSE",
                status=StatutActivite.SOUMISE.name,
                uuid="9c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="UclCourse",
                ects=5,
            ),
            Mock(
                category="PAPER",
                status=StatutActivite.SOUMISE.name,
                uuid="bc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                type="CONFIRMATION_PAPER",
                ects=5,
            ),
            Mock(
                category="SERVICE",
                status=StatutActivite.SOUMISE.name,
                uuid="cc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                type="CONFIRMATION_PAPER",
                ects=5,
            ),
            Mock(
                category="PAPER",
                status=StatutActivite.SOUMISE.name,
                uuid="dc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                ects=5,
            ),
            Mock(
                category="RESIDENCY",
                status=StatutActivite.SOUMISE.name,
                uuid="dc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Residency",
                ects=8,
            ),
        ]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, "L-CDAR24-0000-0002")
        self.assertContains(response, "45")

    def test_complementary_training_list(self):
        url = resolve_url("parcours_doctoral:complementary-training", pk=self.doctorate_uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "L-CDAR24-0000-0002")

    def test_course_enrollment_list(self):
        url = resolve_url("parcours_doctoral:course-enrollment", pk=self.doctorate_uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "L-CDAR24-0000-0002")

    def test_create_wrong_category(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:add",
            pk=self.doctorate_uuid,
            category="UNKNOWN",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:add",
            pk=self.doctorate_uuid,
            category=CategorieActivite.CONFERENCE.name,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, _("Add a conference"))

        data = {
            'ects': 10,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 2.0,
            'hour_volume': '3',
            'city': '',
            'organizing_institution': '',
            'website': '',
            'is_online': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-created')

    def test_create_paper(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:add",
            pk=self.doctorate_uuid,
            category=CategorieActivite.PAPER.name,
        )

        available_papers = [
            ChoixTypeEpreuve.CONFIRMATION_PAPER.name,
            ChoixTypeEpreuve.PUBLIC_DEFENSE.name,
            ChoixTypeEpreuve.PRIVATE_DEFENSE.name,
        ]

        self.mock_doctorate_api.return_value.retrieve_doctoral_training_config.return_value = MagicMock(
            creatable_papers_types=available_papers,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertCountEqual(
            form.fields['type'].choices,
            ((enum_value, ChoixTypeEpreuve[enum_value].value) for enum_value in available_papers),
        )

        self.assertNotIn(
            str(_('A paper of each type has already been created.')),
            response.rendered_content,
        )

        while available_papers:
            available_papers.pop()

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']

            self.assertCountEqual(
                form.fields['type'].choices,
                ((enum_value, ChoixTypeEpreuve[enum_value].value) for enum_value in available_papers),
            )

        self.assertIn(
            str(_('A paper of each type has already been created.')),
            response.rendered_content,
        )

    def test_update_paper(self):
        self.mock_doctorate_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.PAPER.name,
            title="Paper",
            ects=10,
            comment='C1',
            type=ChoixTypeEpreuve.CONFIRMATION_PAPER.name,
            to_dict=Mock(
                return_value=dict(
                    category=CategorieActivite.PAPER.name,
                    title="Paper",
                    ects=10,
                    comment='C2',
                    type=ChoixTypeEpreuve.CONFIRMATION_PAPER.name,
                )
            ),
        )

        url = resolve_url(
            "parcours_doctoral:doctoral-training:edit",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )

        available_papers = []

        self.mock_doctorate_api.return_value.retrieve_doctoral_training_config.return_value = MagicMock(
            creatable_papers_types=available_papers,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertCountEqual(
            form.fields['type'].choices,
            (
                (enum_value, ChoixTypeEpreuve[enum_value].value)
                for enum_value in [
                    ChoixTypeEpreuve.CONFIRMATION_PAPER.name,
                ]
            ),
        )

        response = self.client.post(
            url,
            data={
                'ects': 20,
                'type': ChoixTypeEpreuve.CONFIRMATION_PAPER.name,
                'comment': 'c1',
            },
        )

        self.assertEqual(response.status_code, 302)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.update_training.assert_called()
        self.mock_doctorate_api.return_value.update_training.assert_called_with(
            uuid=self.doctorate_uuid,
            activity_id='64d2e9e3-2537-4a12-a396-48763c5cdc60',
            doctoral_training_activity=Paper(
                object_type='Paper',
                category=CategorieActiviteModel(CategorieActivite.PAPER.name),
                context=ContexteFormationModel(ContexteFormation.DOCTORAL_TRAINING.name),
                type=ChoixTypeEpreuveModel(ChoixTypeEpreuve.CONFIRMATION_PAPER.name),
                ects=20.0,
                comment='c1',
                parent=None,
            ),
            **self.api_default_params,
        )

    def test_create_wrong_dates(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:add",
            pk=self.doctorate_uuid,
            category=CategorieActivite.CONFERENCE.name,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, _("Add a conference"))

        data = {
            'type': 'A great conference',
            'start_date': '13/04/2023',
            'end_date': '12/04/2023',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, "form", 'start_date', _("The start date must be earlier than or the same as the end date.")
        )

    def test_create_with_parent(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:add",
            pk=self.doctorate_uuid,
            category=CategorieActivite.COMMUNICATION.name,
        )
        response = self.client.get(f"{url}?parent=uuid-parent")
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        url = resolve_url(
            "parcours_doctoral:doctoral-training:edit",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Edit"))

        data = {
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 2.0,
            'hour_volume': '3',
            'city': '',
            'organizing_institution': '',
            'website': '',
            'is_online': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-edited')

    def test_update_child(self):
        def side_effect(*args, **kwargs):
            if kwargs['activity_id'] == "64d2e9e3-2537-4a12-a396-48763c5cdc60":
                return Mock(
                    to_dict=Mock(
                        return_value=dict(
                            category="COMMUNICATION",
                            title="child",
                            parent="uuid-parent",
                            type="",
                            participating_proof=[],
                            status=StatutActivite.NON_SOUMISE.name,
                        )
                    )
                )
            return Mock(
                category=CategorieActivite.CONFERENCE.name,
                title="parent",
            )

        self.mock_doctorate_api.return_value.retrieve_training.side_effect = side_effect

        url = resolve_url(
            "parcours_doctoral:doctoral-training:edit",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Edit the communication of this conference"))

        data = {
            'ects': 0,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 0.0,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-edited')

    def test_submit(self):
        activity_mock = Mock(uuid='test', ects=10)
        activity_mock.get = dict(uuid='test', ects=10).get
        self.mock_doctorate_api.return_value.list_doctoral_training.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        self.mock_doctorate_api.return_value.submit_training.return_value = data
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

    def test_submit_with_errors(self):
        activity_mock = Mock(uuid='test', ects=10)
        activity_mock.get = dict(uuid='test', ects=10).get
        self.mock_doctorate_api.return_value.list_doctoral_training.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        # Exception related to an activity
        self.mock_doctorate_api.return_value.submit_training.side_effect = ApiException(
            http_resp=Mock(
                status=400,
                data='{"errors":[{"activite_id": "test", "detail": "Pas bon", "status_code": 0}]}',
            ),
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "activities_form", None, "Pas bon")

        # Any other exception
        self.mock_doctorate_api.return_value.submit_training.side_effect = ApiException(
            http_resp=Mock(
                status=502,
            ),
        )
        with self.assertRaises(ApiException):
            self.client.post(self.url, data)

    @patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
    @patch('osis_learning_unit_sdk.api.learning_units_api.LearningUnitsApi')
    def test_update_course_enrollment(self, learning_unit_api, acad_api):
        learning_unit_api.return_value.learningunitstitle_read.return_value = {'title': "dumb text"}
        current_year = datetime.date.today().year
        acad_api.return_value.get_academic_years.return_value = Mock(
            results=[
                Mock(
                    start_date=datetime.date(current_year, 9, 2),
                    end_date=datetime.date(current_year + 1, 9, 1),
                    year=current_year,
                )
            ]
        )
        url = resolve_url(
            "parcours_doctoral:course-enrollment:edit",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.UCL_COURSE.name,
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.UCL_COURSE.name,
            learning_unit_year='ESA2004',
            learning_unit_title='Something',
            academic_year=current_year,
            academic_year_title="2022-2023",
        )
        response = self.client.post(
            url,
            data={
                'context': ContexteFormation.FREE_COURSE.name,
                'academic_year': current_year,
                'learning_unit_year': 'ESA2004',
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_assent(self):
        url = resolve_url(
            "parcours_doctoral:course-enrollment:assent",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        activity_data = dict(
            object_type="Communication",
            title="Foo bar",
            category=CategorieActivite.COMMUNICATION.name,
            reference_promoter_assent=None,
            reference_promoter_comment="",
            status=[StatutActivite.SOUMISE.name],
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value = Mock(**activity_data)
        self.mock_doctorate_api.return_value.retrieve_training.return_value.to_dict.return_value = activity_data
        response = self.client.get(url)
        self.assertContains(response, "dependsOn.min.js", count=1)
        self.assertContains(response, "Foo bar")
        data = {
            'approbation': True,
            'commentaire': "Ok",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_delete(self):
        url = resolve_url(
            "parcours_doctoral:course-enrollment:delete",
            pk=self.doctorate_uuid,
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.UCL_COURSE.name,
        )
        self.mock_doctorate_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.UCL_COURSE.name,
            reference_promoter_assent=None,
            reference_promoter_comment="",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
