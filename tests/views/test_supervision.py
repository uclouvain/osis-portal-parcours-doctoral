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
from osis_parcours_doctoral_sdk.model.supervision_dto import SupervisionDTO
from osis_parcours_doctoral_sdk.model.supervision_dto_promoteur import SupervisionDTOPromoteur
from osis_parcours_doctoral_sdk.model.supervision_dto_signatures_membres_ca import SupervisionDTOSignaturesMembresCA
from osis_parcours_doctoral_sdk.model.supervision_dto_signatures_promoteurs import SupervisionDTOSignaturesPromoteurs

from parcours_doctoral.contrib.enums.actor import ChoixEtatSignature
from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class SupervisionTestCase(BaseDoctorateTestCase):
    def setUp(self):
        super().setUp()

        self.detail_url = resolve_url("parcours_doctoral:supervision", pk=self.doctorate_uuid)

        self.mock_doctorate_api.return_value.retrieve_supervision.return_value = SupervisionDTO._from_openapi_data(
            signatures_promoteurs=[
                SupervisionDTOSignaturesPromoteurs._from_openapi_data(
                    promoteur=SupervisionDTOPromoteur._from_openapi_data(
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
                SupervisionDTOSignaturesPromoteurs._from_openapi_data(
                    promoteur=SupervisionDTOPromoteur._from_openapi_data(
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
                SupervisionDTOSignaturesPromoteurs._from_openapi_data(
                    promoteur=SupervisionDTOPromoteur._from_openapi_data(
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
                SupervisionDTOSignaturesMembresCA._from_openapi_data(
                    membre_ca=SupervisionDTOPromoteur._from_openapi_data(
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

    def test_should_detail_supervision_member(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.detail_url)

        # Display the signatures
        self.assertContains(response, "Troufignon")
        self.assertContains(response, ChoixEtatSignature.APPROVED.value)
        self.assertContains(response, "A public comment to display")
        self.assertContains(response, ChoixEtatSignature.DECLINED.value)
        self.mock_doctorate_api.return_value.retrieve_supervision.assert_called()
