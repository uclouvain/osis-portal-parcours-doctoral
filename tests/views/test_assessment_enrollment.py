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
import uuid

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.inscription_evaluation_dto import (
    InscriptionEvaluationDTO,
)

from parcours_doctoral.contrib.enums import Session, StatutInscriptionEvaluation
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class AssessmentEnrollmentListViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:assessment-enrollment', pk=cls.doctorate_uuid)

        cls.enrollments = [
            InscriptionEvaluationDTO._from_openapi_data(
                uuid=str(uuid.uuid4()),
                session=Session.JANUARY.name,
                inscription_tardive=False,
                uuid_activite=str(uuid.uuid4()),
                statut=StatutInscriptionEvaluation.ACCEPTEE.name,
                code_unite_enseignement='ABC',
                intitule_unite_enseignement='I1',
                annee_unite_enseignement=2020,
            ),
            InscriptionEvaluationDTO._from_openapi_data(
                uuid=str(uuid.uuid4()),
                session=Session.JANUARY.name,
                inscription_tardive=False,
                uuid_activite=str(uuid.uuid4()),
                statut=StatutInscriptionEvaluation.DESINSCRITE.name,
                code_unite_enseignement='DEF',
                intitule_unite_enseignement='I2',
                annee_unite_enseignement=2020,
            ),
            InscriptionEvaluationDTO._from_openapi_data(
                uuid=str(uuid.uuid4()),
                session=Session.JUNE.name,
                inscription_tardive=False,
                uuid_activite=str(uuid.uuid4()),
                statut=StatutInscriptionEvaluation.ACCEPTEE.name,
                code_unite_enseignement='GHI',
                intitule_unite_enseignement='I3',
                annee_unite_enseignement=2021,
            ),
        ]

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.list_inscription_evaluation_dtos.return_value = self.enrollments

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_assessment_enrollment'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_assessment_enrollments(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the enrollments information
        self.mock_doctorate_api.return_value.list_inscription_evaluation_dtos.assert_called()

        assessment_enrollments = response.context['assessment_enrollments']

        self.assertEqual(len(assessment_enrollments), 2)
        self.assertEqual([2020, 2021], list(assessment_enrollments.keys()))

        self.assertEqual([Session.JANUARY.name], list(assessment_enrollments[2020].keys()))
        self.assertEqual(len(assessment_enrollments[2020][Session.JANUARY.name]), 2)

        self.assertEqual(assessment_enrollments[2020][Session.JANUARY.name][0].uuid, self.enrollments[0].uuid)
        self.assertEqual(assessment_enrollments[2020][Session.JANUARY.name][1].uuid, self.enrollments[1].uuid)

        self.assertEqual([Session.JUNE.name], list(assessment_enrollments[2021].keys()))
        self.assertEqual(len(assessment_enrollments[2021][Session.JUNE.name]), 1)
        self.assertEqual(assessment_enrollments[2021][Session.JUNE.name][0].uuid, self.enrollments[2].uuid)


class AssessmentEnrollmentDetailsViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.enrollment = InscriptionEvaluationDTO._from_openapi_data(
            uuid=str(uuid.uuid4()),
            session=Session.JANUARY.name,
            inscription_tardive=False,
            uuid_activite=str(uuid.uuid4()),
            statut=StatutInscriptionEvaluation.ACCEPTEE.name,
            code_unite_enseignement='ABC',
            intitule_unite_enseignement='I1',
            annee_unite_enseignement=2020,
        )

        cls.url = resolve_url(
            'parcours_doctoral:assessment-enrollment:details',
            pk=cls.doctorate_uuid,
            enrollment_uuid=cls.enrollment.uuid,
        )

    def setUp(self):
        super().setUp()

        self.mock_doctorate_api.return_value.retrieve_inscription_evaluation_dto.return_value = self.enrollment

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_assessment_enrollment'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_assessment_enrollment(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.retrieve_parcours_doctoral_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the enrollment information
        self.mock_doctorate_api.return_value.retrieve_inscription_evaluation_dto.assert_called()

        assessment_enrollment = response.context['assessment_enrollment']

        self.assertEqual(assessment_enrollment.uuid, self.enrollment.uuid)
