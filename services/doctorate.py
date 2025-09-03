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

from enum import Enum
from typing import List

import osis_parcours_doctoral_sdk
from django.conf import settings
from django.utils.translation import get_language
from osis_parcours_doctoral_sdk import ApiException
from osis_parcours_doctoral_sdk.api import doctorate_api
from osis_parcours_doctoral_sdk.model.approuver_jury_command import ApprouverJuryCommand
from osis_parcours_doctoral_sdk.model.approuver_jury_par_pdf_command import (
    ApprouverJuryParPdfCommand,
)
from osis_parcours_doctoral_sdk.model.confirmation_paper_canvas import (
    ConfirmationPaperCanvas,
)
from osis_parcours_doctoral_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO
from osis_parcours_doctoral_sdk.model.jury_dto import JuryDTO
from osis_parcours_doctoral_sdk.model.membre_jury_identity_dto import (
    MembreJuryIdentityDTO,
)
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto import ParcoursDoctoralDTO
from osis_parcours_doctoral_sdk.model.parcours_doctoral_identity_dto import (
    ParcoursDoctoralIdentityDTO,
)
from osis_parcours_doctoral_sdk.model.refuser_jury_command import RefuserJuryCommand
from osis_parcours_doctoral_sdk.model.renvoyer_invitation_signature_externe import (
    RenvoyerInvitationSignatureExterne,
)
from osis_parcours_doctoral_sdk.model.supervision_canvas import SupervisionCanvas
from osis_parcours_doctoral_sdk.model.supervision_dto import SupervisionDTO

from base.models.person import Person
from frontoffice.settings.osis_sdk import parcours_doctoral as parcours_doctoral_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from parcours_doctoral.services.mixins import ServiceMeta

__all__ = [
    "DoctorateService",
    "DoctorateSupervisionService",
    "ExternalDoctorateService",
    "ParcoursDoctoralBusinessException",
]


class DoctorateAPIClient:
    def __new__(cls, api_config=None):
        api_config = api_config or parcours_doctoral_sdk.build_configuration()
        return doctorate_api.DoctorateApi(osis_parcours_doctoral_sdk.ApiClient(configuration=api_config))


class DoctorateService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_dashboard_links(cls, person: Person):
        return (
            DoctorateAPIClient()
            .retrieve_dashboard(
                **build_mandatory_auth_headers(person),
            )
            .to_dict()
            .get('links', {})
        )

    @classmethod
    def get_doctorates(cls, person: Person):
        return DoctorateAPIClient().list_doctorates(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_supervised_doctorates(cls, person: Person):
        return DoctorateAPIClient().list_supervised_doctorates(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_funding(cls, person: Person, uuid_doctorate, data):
        return DoctorateAPIClient().update_funding(
            uuid=uuid_doctorate,
            modifier_financement_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_cotutelle(cls, person: Person, uuid_doctorate, data):
        return DoctorateAPIClient().update_cotutelle(
            uuid=uuid_doctorate,
            modifier_cotutelle_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_supervision(cls, person, uuid_doctorate) -> SupervisionDTO:
        return DoctorateAPIClient().retrieve_supervision(
            uuid=uuid_doctorate,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_supervision_canvas(cls, person, uuid_doctorate) -> SupervisionCanvas:
        return DoctorateAPIClient().retrieve_supervision_canvas(
            uuid=uuid_doctorate,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_training_recap_pdf(cls, person, uuid_doctorate) -> SupervisionCanvas:
        return DoctorateAPIClient().training_recap_pdf(
            uuid=uuid_doctorate,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_doctorate(cls, person, uuid) -> ParcoursDoctoralDTO:
        return DoctorateAPIClient().doctorate_retrieve(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_confirmation_papers(cls, person, uuid) -> List[ConfirmationPaperDTO]:
        return DoctorateAPIClient().retrieve_confirmation_papers(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper(cls, person, uuid) -> ConfirmationPaperDTO:
        return DoctorateAPIClient().retrieve_last_confirmation_paper(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper_canvas(cls, person, uuid) -> ConfirmationPaperCanvas:
        return DoctorateAPIClient().retrieve_last_confirmation_paper_canvas(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper(cls, person, uuid, **kwargs) -> ParcoursDoctoralIdentityDTO:
        return DoctorateAPIClient().submit_confirmation_paper(
            uuid=uuid,
            submit_confirmation_paper_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def complete_confirmation_paper_by_promoter(cls, person, uuid, **kwargs) -> ParcoursDoctoralIdentityDTO:
        return DoctorateAPIClient().complete_confirmation_paper_by_promoter(
            uuid=uuid,
            complete_confirmation_paper_by_promoter_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper_extension_request(cls, person, uuid, **kwargs) -> ParcoursDoctoralIdentityDTO:
        return DoctorateAPIClient().submit_confirmation_paper_extension_request(
            uuid=uuid,
            submit_confirmation_paper_extension_request_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class ExternalDoctorateService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_parcours_doctoral_sdk.Configuration(
            host=settings.OSIS_PARCOURS_DOCTORAL_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.PARCOURS_DOCTORAL_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def get_supervision(cls, uuid, token):
        api_client = DoctorateAPIClient(api_config=cls.build_config())
        return api_client.retrieve_external_doctorate_supervision(
            uuid=uuid,
            token=token,
            **cls.build_mandatory_external_headers(),
        )


class DoctorateSupervisionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_parcours_doctoral_sdk.Configuration(
            host=settings.OSIS_PARCOURS_DOCTORAL_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.PARCOURS_DOCTORAL_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def get_supervision(cls, person, uuid) -> SupervisionDTO:
        return DoctorateAPIClient().retrieve_supervision(uuid=uuid, **build_mandatory_auth_headers(person))

    @classmethod
    def get_external_supervision(cls, uuid, token):
        return DoctorateAPIClient(api_config=cls.build_config()).get_external_proposition(
            uuid=uuid,
            token=token,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def get_signature_conditions(cls, person, uuid) -> SupervisionDTO:
        return DoctorateAPIClient().retrieve_verify_project(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def add_member(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().add_member(
            uuid=uuid,
            identifier_supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def edit_external_member(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().edit_external_member(
            uuid=uuid,
            modifier_membre_supervision_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_member(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().remove_member(
            uuid=uuid,
            supervision_actor_reference=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def set_reference_promoter(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().set_reference_promoter(
            uuid=uuid,
            designer_promoteur_reference_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def resend_invite(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().update_signatures(
            uuid=uuid,
            renvoyer_invitation_signature_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_proposition(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().approve_proposition(
            uuid=uuid,
            approuver_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def reject_proposition(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().reject_proposition(
            uuid=uuid,
            refuser_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_external_proposition(cls, uuid, token, **kwargs):
        return DoctorateAPIClient(api_config=cls.build_config()).approve_external_proposition(
            uuid=uuid,
            token=token,
            approuver_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def reject_external_proposition(cls, uuid, token, **kwargs):
        return DoctorateAPIClient(api_config=cls.build_config()).reject_external_proposition(
            uuid=uuid,
            token=token,
            refuser_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def approve_by_pdf(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().approve_by_pdf(
            uuid=uuid,
            approuver_proposition_par_pdf_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class DoctorateJuryService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_parcours_doctoral_sdk.Configuration(
            host=settings.OSIS_PARCOURS_DOCTORAL_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.PARCOURS_DOCTORAL_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def retrieve_jury(cls, person, uuid, **kwargs) -> JuryDTO:
        return DoctorateAPIClient().retrieve_jury_preparation(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def modifier_jury(cls, person, uuid, **kwargs) -> JuryDTO:
        return DoctorateAPIClient().update_jury_preparation(
            uuid=uuid,
            modifier_jury_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_jury_members(cls, person, uuid, **kwargs) -> List[MembreJuryIdentityDTO]:
        return DoctorateAPIClient().list_jury_members(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_jury_member(cls, person, uuid, **kwargs) -> MembreJuryIdentityDTO:
        return DoctorateAPIClient().create_jury_members(
            uuid=uuid,
            ajouter_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return DoctorateAPIClient().retrieve_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return DoctorateAPIClient().remove_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return DoctorateAPIClient().update_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            modifier_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_role_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return DoctorateAPIClient().update_role_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            patched_modifier_role_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def request_signatures(cls, person: Person, uuid):
        return DoctorateAPIClient().request_signatures(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_signature_conditions(cls, person, uuid) -> List:
        return DoctorateAPIClient().signature_conditions(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def resend_invite(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().resend_invite(
            uuid=uuid,
            renvoyer_invitation_signature_externe=RenvoyerInvitationSignatureExterne(**kwargs),
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_jury(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().approve_jury(
            uuid=uuid,
            approuver_jury_command=ApprouverJuryCommand(**kwargs),
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def reject_jury(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().reject_jury(
            uuid=uuid,
            refuser_jury_command=RefuserJuryCommand(**kwargs),
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_external_jury(cls, uuid, token, **kwargs):
        return DoctorateAPIClient(api_config=cls.build_config()).get_external_jury(
            uuid=uuid,
            token=token,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def approve_external_jury(cls, uuid, token, **kwargs):
        return DoctorateAPIClient(api_config=cls.build_config()).approve_external_jury(
            uuid=uuid,
            token=token,
            approuver_jury_command=ApprouverJuryCommand(**kwargs),
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def reject_external_jury(cls, uuid, token, **kwargs):
        return DoctorateAPIClient(api_config=cls.build_config()).reject_external_jury(
            uuid=uuid,
            token=token,
            refuser_jury_command=RefuserJuryCommand(**kwargs),
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def approve_by_pdf(cls, person, uuid, **kwargs):
        return DoctorateAPIClient().approve_by_pdf(
            uuid=uuid,
            approuver_jury_par_pdf_command=ApprouverJuryParPdfCommand(**kwargs),
            **build_mandatory_auth_headers(person),
        )


class ParcoursDoctoralBusinessException(Enum):
    ParcoursDoctoralNonTrouveException = "PARCOURS-DOCTORAL-1"
    PromoteurNonTrouveException = "PARCOURS-DOCTORAL-2"
    MembreCANonTrouveException = "PARCOURS-DOCTORAL-3"
    SignataireNonTrouveException = "PARCOURS-DOCTORAL-4"
    SignataireDejaInviteException = "PARCOURS-DOCTORAL-5"
    SignatairePasInviteException = "PARCOURS-DOCTORAL-6"
    MembreSoitInterneSoitExterneException = "PARCOURS-DOCTORAL-7"
    DejaMembreException = "PARCOURS-DOCTORAL-8"
    ProcedureDemandeSignatureNonLanceeException = "PARCOURS-DOCTORAL-9"
    PropositionNonApprouveeParPromoteurException = "PARCOURS-DOCTORAL-10"
    PropositionNonApprouveeParMembresCAException = "PARCOURS-DOCTORAL-11"
    PromoteurManquantException = "PARCOURS-DOCTORAL-12"
    MembreCAManquantException = "PARCOURS-DOCTORAL-13"
    ProcedureDemandeSignatureLanceeException = "PARCOURS-DOCTORAL-14"
    PropositionNonEnAttenteDeSignatureException = "PARCOURS-DOCTORAL-15"
    PromoteurDeReferenceManquantException = "PARCOURS-DOCTORAL-16"
    GroupeSupervisionCompletPourPromoteursException = "PARCOURS-DOCTORAL-17"
    GroupeSupervisionCompletPourMembresCAException = "PARCOURS-DOCTORAL-18"
    GroupeDeSupervisionNonTrouveException = "PARCOURS-DOCTORAL-19"
    DomaineTheseInconsistantException = "PARCOURS-DOCTORAL-20"
    ContratTravailInconsistantException = "PARCOURS-DOCTORAL-21"
    InstitutionInconsistanteException = "PARCOURS-DOCTORAL-22"


class ConfirmationPaperBusinessException(Enum):
    EpreuveConfirmationNonTrouveeException = "EPREUVE-CONFIRMATION-1"
    EpreuveConfirmationNonCompleteeException = "EPREUVE-CONFIRMATION-2"
    EpreuveConfirmationDateIncorrecteException = "EPREUVE-CONFIRMATION-3"
    DemandeProlongationNonCompleteeException = "EPREUVE-CONFIRMATION-4"
    AvisProlongationNonCompleteException = "EPREUVE-CONFIRMATION-5"
    DemandeProlongationNonDefinieException = "EPREUVE-CONFIRMATION-6"
    EpreuveConfirmationNonCompleteePourEvaluationException = "EPREUVE-CONFIRMATION-7"


class JuryBusinessException(Enum):
    PromoteurPresidentException = "JURY-1"
    MembreNonTrouveDansJuryException = "JURY-3"
    JuryNonTrouveException = "JURY-4"
    PromoteurRetireException = "JURY-5"
    PromoteurModifieException = "JURY-6"
    NonDocteurSansJustificationException = "JURY-7"
    MembreExterneSansInstitutionException = "JURY-8"
    MembreExterneSansPaysException = "JURY-9"
    MembreExterneSansNomException = "JURY-10"
    MembreExterneSansPrenomException = "JURY-11"
    MembreExterneSansTitreException = "JURY-12"
    MembreExterneSansGenreException = "JURY-13"
    MembreExterneSansEmailException = "JURY-14"
    MembreDejaDansJuryException = "JURY-15"
