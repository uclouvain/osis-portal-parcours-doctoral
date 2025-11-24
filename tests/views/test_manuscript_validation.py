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
from osis_parcours_doctoral_sdk.model.accept_thesis_by_lead_promoter import (
    AcceptThesisByLeadPromoter,
)
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.authorization_distribution_dto import (
    AuthorizationDistributionDTO,
)
from osis_parcours_doctoral_sdk.model.reject_thesis_by_lead_promoter import (
    RejectThesisByLeadPromoter,
)
from osis_parcours_doctoral_sdk.model.signataire_autorisation_diffusion_these_dto_nested import (
    SignataireAutorisationDiffusionTheseDTONested,
)
from osis_parcours_doctoral_sdk.model.signature_autorisation_diffusion_these_dto_nested import (
    SignatureAutorisationDiffusionTheseDTONested,
)

from base.tests.factories.person import PersonFactory
from parcours_doctoral.constants import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.contrib.enums import (
    ChoixEtatSignature,
    DecisionApprovalEnum,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.contrib.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class ManuscriptValidationDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url('parcours_doctoral:manuscript-validation', pk=cls.doctorate_uuid)

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
                signataires=[
                    SignataireAutorisationDiffusionTheseDTONested._from_openapi_data(
                        uuid=str(uuid.uuid4()),
                        matricule='0123456789',
                        prenom='John',
                        nom='Doe',
                        email='john.doe@uclouvain.be',
                        genre='H',
                        institution='UCLouvain',
                        role=RoleActeur.PROMOTEUR.name,
                        signature=SignatureAutorisationDiffusionTheseDTONested._from_openapi_data(
                            etat=ChoixEtatSignature.INVITED.name,
                            date_heure=datetime.datetime(2025, 1, 1, 11, 30),
                            commentaire_externe='External comment',
                            commentaire_interne='Internal comment',
                            motif_refus='Refusal reason',
                        ),
                    )
                ],
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

    def test_get_manuscript_validation_data(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the manuscript validation information
        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.assert_called()

        self.assertIsNotNone(response.context.get('authorization_distribution'))
        self.assertEqual(response.context.get('authorization_distribution').uuid, self.doctorate_uuid)

        self.assertIsNotNone(response.context.get('signatories'))
        self.assertIsNotNone(response.context['signatories']['PROMOTEUR'])
        self.assertEqual(response.context['signatories']['PROMOTEUR'].matricule, '0123456789')


class ManuscriptValidationFormViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.person = PersonFactory()
        cls.url = resolve_url('parcours_doctoral:update:manuscript-validation', pk=cls.doctorate_uuid)
        cls.details_url = resolve_url('parcours_doctoral:manuscript-validation', pk=cls.doctorate_uuid)

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
                signataires=[
                    SignataireAutorisationDiffusionTheseDTONested._from_openapi_data(
                        uuid=str(uuid.uuid4()),
                        matricule='0123456789',
                        prenom='John',
                        nom='Doe',
                        email='john.doe@uclouvain.be',
                        genre='H',
                        institution='UCLouvain',
                        role=RoleActeur.PROMOTEUR.name,
                        signature=SignatureAutorisationDiffusionTheseDTONested._from_openapi_data(
                            etat=ChoixEtatSignature.INVITED.name,
                            date_heure=datetime.datetime(2025, 1, 1, 11, 30),
                            commentaire_externe='External comment',
                            commentaire_interne='Internal comment',
                            motif_refus='Refusal reason',
                        ),
                    )
                ],
                date_embargo=datetime.date(2025, 1, 1),
                modalites_diffusion_acceptees_le=datetime.date(2024, 1, 1),
            )
        )

    def test_get_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['validate_manuscript'] = ActionLink._from_openapi_data(
            error='access error',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_manuscript_validation_data(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_doctorate_api.return_value.doctorate_retrieve.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, self.doctorate_uuid)

        # Load the manuscript validation information
        self.mock_doctorate_api.return_value.retrieve_authorization_distribution.assert_called()

        self.assertIsNotNone(response.context.get('authorization_distribution'))
        self.assertEqual(response.context.get('authorization_distribution').uuid, self.doctorate_uuid)

        self.assertIsNotNone(response.context.get('signatories'))
        self.assertIsNotNone(response.context['signatories']['PROMOTEUR'])
        self.assertEqual(response.context['signatories']['PROMOTEUR'].matricule, '0123456789')

        self.assertIsInstance(response.context.get('form'), ManuscriptValidationApprovalForm)

    def test_post_invalid_manuscript_validation_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors.get('decision'), [FIELD_REQUIRED_MESSAGE])

        response = self.client.post(self.url, data={'decision': DecisionApprovalEnum.DECLINED.name})

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors.get('motif_refus'), [FIELD_REQUIRED_MESSAGE])

    def test_post_valid_manuscript_validation_reject_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={
                'decision': DecisionApprovalEnum.DECLINED.name,
                'motif_refus': 'Refusal reason',
                'commentaire_interne': 'Internal comment',
                'commentaire_externe': 'External comment',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.reject_thesis_by_lead_promoter.assert_called()
        self.mock_doctorate_api.return_value.reject_thesis_by_lead_promoter.assert_called_with(
            uuid=self.doctorate_uuid,
            reject_thesis_by_lead_promoter=RejectThesisByLeadPromoter._new_from_openapi_data(
                motif_refus='Refusal reason',
                commentaire_interne='Internal comment',
                commentaire_externe='External comment',
            ),
            **self.api_default_params,
        )

    def test_post_valid_manuscript_validation_accept_data(self):
        self.client.force_login(self.person.user)

        response = self.client.post(
            self.url,
            data={
                'decision': DecisionApprovalEnum.APPROVED.name,
                'motif_refus': 'Refusal reason',
                'commentaire_interne': 'Internal comment',
                'commentaire_externe': 'External comment',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Call the API with the right data
        self.mock_doctorate_api.return_value.accept_thesis_by_lead_promoter.assert_called()
        self.mock_doctorate_api.return_value.accept_thesis_by_lead_promoter.assert_called_with(
            uuid=self.doctorate_uuid,
            accept_thesis_by_lead_promoter=AcceptThesisByLeadPromoter._new_from_openapi_data(
                commentaire_interne='Internal comment',
                commentaire_externe='External comment',
            ),
            **self.api_default_params,
        )
