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

from django.shortcuts import resolve_url
from osis_parcours_doctoral_sdk.models.action_link import ActionLink
from osis_parcours_doctoral_sdk.models.membre_cadto_nested import MembreCADTONested
from osis_parcours_doctoral_sdk.models.promoteur_dto_nested import PromoteurDTONested
from osis_parcours_doctoral_sdk.models.supervision_canvas import SupervisionCanvas
from osis_parcours_doctoral_sdk.models.supervision_dto import SupervisionDTO
from osis_parcours_doctoral_sdk.models.detail_signature_membre_cadto_nested import (
    DetailSignatureMembreCADTONested,
)
from osis_parcours_doctoral_sdk.models.detail_signature_promoteur_dto_nested import (
    DetailSignaturePromoteurDTONested,
)

from parcours_doctoral.contrib.enums.actor import ChoixEtatSignature
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class SupervisionTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.detail_url = resolve_url("parcours_doctoral:supervision", pk=self.doctorate_uuid)

        self.mock_doctorate_api.return_value.retrieve_supervision.return_value = SupervisionDTO._from_openapi_data(
            signatures_promoteurs=[
                DetailSignaturePromoteurDTONested._from_openapi_data(
                    promoteur=PromoteurDTONested._from_openapi_data(
                        uuid="uuid-0123456978",
                        matricule="0123456978",
                        prenom="Marie-Odile",
                        nom="Troufignon",
                        est_docteur=True,
                        email="",
                        institution="",
                        ville="",
                        code_pays="",
                        pays="",
                        est_externe=False,
                    ),
                    pdf=[],
                    statut=ChoixEtatSignature.APPROVED.name,
                    commentaire_externe="A public comment to display",
                ),
                DetailSignaturePromoteurDTONested._from_openapi_data(
                    promoteur=PromoteurDTONested._from_openapi_data(
                        uuid="uuid-9876543210",
                        matricule="9876543210",
                        prenom="John",
                        nom="Doe",
                        est_docteur=True,
                        email="",
                        institution="",
                        ville="",
                        code_pays="",
                        pays="",
                        est_externe=False,
                    ),
                    pdf=[],
                    statut=ChoixEtatSignature.DECLINED.name,
                    commentaire_externe="A public comment to display",
                ),
                DetailSignaturePromoteurDTONested._from_openapi_data(
                    promoteur=PromoteurDTONested._from_openapi_data(
                        uuid="uuid-externe",
                        matricule="",
                        prenom="Marcel",
                        nom="Troufignon",
                        est_docteur=True,
                        email="marcel@example.org",
                        institution="isntitution",
                        ville="ville",
                        code_pays="FR",
                        pays="France",
                        est_externe=True,
                    ),
                    pdf=[],
                    statut=ChoixEtatSignature.APPROVED.name,
                    commentaire_externe="",
                ),
            ],
            signatures_membres_ca=[
                DetailSignatureMembreCADTONested._from_openapi_data(
                    membre_ca=MembreCADTONested._from_openapi_data(
                        uuid=f"uuid-{self.person.global_id}",
                        matricule=self.person.global_id,
                        prenom="Jacques-Eudes",
                        nom="Birlimpette",
                        est_docteur=True,
                        email="",
                        institution="",
                        ville="",
                        code_pays="",
                        pays="",
                        est_externe=False,
                    ),
                    pdf=[],
                    statut=ChoixEtatSignature.INVITED.name,
                ),
            ],
            promoteur_reference="uuid-0123456978",
        )

    def test_should_return_permission_denied_if_no_access(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.links['retrieve_supervision'] = ActionLink._from_openapi_data(error='access error')

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 403)

    def test_should_detail_supervision_member(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.detail_url)

        # Display the signatures
        self.assertContains(response, "Troufignon")
        self.assertContains(response, ChoixEtatSignature.APPROVED.value)
        self.assertContains(response, "A public comment to display")
        self.assertContains(response, ChoixEtatSignature.DECLINED.value)
        self.mock_doctorate_api.return_value.retrieve_supervision.assert_called()

        # Display the link to download the supervision canvas
        canvas_url = resolve_url('parcours_doctoral:supervision-canvas', pk=self.doctorate_uuid)
        self.assertContains(response, canvas_url)

    def test_should_not_display_supervision_canvas_link_if_forbidden(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.links['retrieve_supervision_canvas'] = ActionLink._from_openapi_data(
            error='access error',
        )

        response = self.client.get(self.detail_url)

        # Hide the link to download the supervision canvas
        canvas_url = resolve_url('parcours_doctoral:supervision-canvas', pk=self.doctorate_uuid)
        self.assertNotContains(response, canvas_url)


class SupervisionCanvasTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.canvas_view_url = resolve_url('parcours_doctoral:supervision-canvas', pk=self.doctorate_uuid)
        self.canvas_file_url = resolve_url('parcours_doctoral:project', pk=self.doctorate_uuid)

        self.retrieve_supervision_canvas = self.mock_doctorate_api.return_value.retrieve_supervision_canvas
        self.retrieve_supervision_canvas.return_value = SupervisionCanvas._from_openapi_data(url=self.canvas_file_url)

    def test_should_return_permission_denied_if_no_access(self):
        self.client.force_login(self.person.user)

        self.mock_doctorate_object.links['retrieve_supervision_canvas'] = ActionLink._from_openapi_data(
            error='access error',
        )

        response = self.client.get(self.canvas_view_url)

        self.assertEqual(response.status_code, 403)

    def test_should_redirect_to_canvas_file_url(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.canvas_view_url)

        self.assertRedirects(
            response,
            self.canvas_file_url,
            fetch_redirect_response=False,
        )
