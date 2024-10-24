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

from enum import Enum
from typing import List

from django.conf import settings
from django.utils.translation import get_language

import osis_admission_sdk
from base.models.person import Person
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.confirmation_paper_canvas import ConfirmationPaperCanvas
from osis_admission_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO
from osis_admission_sdk.model.cotutelle_dto import CotutelleDTO
from osis_admission_sdk.model.doctorate_dto import DoctorateDTO
from osis_admission_sdk.model.doctorate_identity_dto import DoctorateIdentityDTO
from osis_admission_sdk.model.doctorate_proposition_dto import DoctoratePropositionDTO
from osis_admission_sdk.model.jury_identity_dto import JuryIdentityDTO
from osis_admission_sdk.model.membre_jury_identity_dto import MembreJuryIdentityDTO
from osis_admission_sdk.model.supervision_dto import SupervisionDTO
from parcours_doctoral.services.mixins import ServiceMeta

__all__ = [
    "DoctorateService",
    "DoctorateCotutelleService",
    "DoctorateSupervisionService",
    "TAB_OF_BUSINESS_EXCEPTION",
    "BUSINESS_EXCEPTIONS_BY_TAB",
    "PropositionBusinessException",
    "GlobalPropositionBusinessException",
]


class APIClient:
    def __new__(cls, api_config=None):
        api_config = api_config or admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class DoctorateService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_dashboard_links(cls, person: Person):
        return APIClient().retrieve_dashboard(**build_mandatory_auth_headers(person)).to_dict().get('links', {})

    @classmethod
    def update_proposition(cls, person: Person, **kwargs):
        return APIClient().update_project(
            uuid=kwargs['uuid'],
            completer_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_proposition(cls, person: Person, uuid) -> DoctoratePropositionDTO:
        return APIClient().retrieve_doctorate_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_propositions(cls, person: Person):
        return APIClient().list_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_supervised_propositions(cls, person: Person):
        return APIClient().list_supervised_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def request_signatures(cls, person: Person, uuid):
        return APIClient().create_signatures(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_doctorate(cls, person, uuid) -> DoctorateDTO:
        return APIClient().retrieve_doctorate_dto(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_confirmation_papers(cls, person, uuid) -> List[ConfirmationPaperDTO]:
        return APIClient().retrieve_confirmation_papers(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper(cls, person, uuid) -> ConfirmationPaperDTO:
        return APIClient().retrieve_last_confirmation_paper(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper_canvas(cls, person, uuid) -> ConfirmationPaperCanvas:
        return APIClient().retrieve_last_confirmation_paper_canvas(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().submit_confirmation_paper(
            uuid=uuid,
            submit_confirmation_paper_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def complete_confirmation_paper_by_promoter(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().complete_confirmation_paper_by_promoter(
            uuid=uuid,
            complete_confirmation_paper_by_promoter_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper_extension_request(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().submit_confirmation_paper_extension_request(
            uuid=uuid,
            submit_confirmation_paper_extension_request_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class ConfirmationPaperBusinessException(Enum):
    EpreuveConfirmationNonTrouveeException = "EPREUVE-CONFIRMATION-1"
    EpreuveConfirmationNonCompleteeException = "EPREUVE-CONFIRMATION-2"
    EpreuveConfirmationDateIncorrecteException = "EPREUVE-CONFIRMATION-3"
    DemandeProlongationNonCompleteeException = "EPREUVE-CONFIRMATION-4"
    AvisProlongationNonCompleteException = "EPREUVE-CONFIRMATION-5"
    DemandeProlongationNonDefinieException = "EPREUVE-CONFIRMATION-6"
    EpreuveConfirmationNonCompleteePourEvaluationException = "EPREUVE-CONFIRMATION-7"


class PropositionBusinessException(Enum):
    MaximumPropositionsAtteintException = "PROPOSITION-1"
    DoctoratNonTrouveException = "PROPOSITION-2"
    PropositionNonTrouveeException = "PROPOSITION-3"
    GroupeDeSupervisionNonTrouveException = "PROPOSITION-4"
    ProximityCommissionInconsistantException = "PROPOSITION-5"
    ContratTravailInconsistantException = "PROPOSITION-6"
    InstitutionInconsistanteException = "PROPOSITION-7"
    DomaineTheseInconsistantException = "PROPOSITION-8"
    PromoteurNonTrouveException = "PROPOSITION-9"
    MembreCANonTrouveException = "PROPOSITION-10"
    SignataireNonTrouveException = "PROPOSITION-11"
    SignataireDejaInviteException = "PROPOSITION-12"
    SignatairePasInviteException = "PROPOSITION-13"
    MembreSoitInterneSoitExterneException = "PROPOSITION-14"
    DejaMembreException = "PROPOSITION-15"
    JustificationRequiseException = "PROPOSITION-16"
    DetailProjetNonCompleteException = "PROPOSITION-17"
    CotutelleNonCompleteException = "PROPOSITION-18"
    PromoteurManquantException = "PROPOSITION-19"
    MembreCAManquantException = "PROPOSITION-20"
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException = "PROPOSITION-21"
    GroupeSupervisionCompletPourPromoteursException = "PROPOSITION-22"
    GroupeSupervisionCompletPourMembresCAException = "PROPOSITION-23"
    CandidatNonTrouveException = "PROPOSITION-24"
    IdentificationNonCompleteeException = "PROPOSITION-25"
    NumeroIdentiteNonSpecifieException = "PROPOSITION-26"
    NumeroIdentiteBelgeNonSpecifieException = "PROPOSITION-27"
    DateOuAnneeNaissanceNonSpecifieeException = "PROPOSITION-28"
    DetailsPasseportNonSpecifiesException = "PROPOSITION-29"
    CarteIdentiteeNonSpecifieeException = "PROPOSITION-30"
    AdresseDomicileLegalNonCompleteeException = "PROPOSITION-31"
    AdresseCorrespondanceNonCompleteeException = "PROPOSITION-32"
    LanguesConnuesNonSpecifieesException = "PROPOSITION-33"
    FichierCurriculumNonRenseigneException = "PROPOSITION-34"
    AnneesCurriculumNonSpecifieesException = "PROPOSITION-35"
    ProcedureDemandeSignatureNonLanceeException = "PROPOSITION-36"
    PropositionNonApprouveeParPromoteurException = "PROPOSITION-37"
    PropositionNonApprouveeParMembresCAException = "PROPOSITION-38"
    InstitutTheseObligatoireException = "PROPOSITION-39"
    NomEtPrenomNonSpecifiesException = "PROPOSITION-40"
    SpecifierNOMASiDejaInscritException = "PROPOSITION-41"
    PromoteurDeReferenceManquantException = "PROPOSITION-42"
    AbsenceDeDetteNonCompleteeException = "PROPOSITION-43"
    ReductionDesDroitsInscriptionNonCompleteeException = "PROPOSITION-44"
    AssimilationNonCompleteeException = "PROPOSITION-45"
    AffiliationsNonCompleteesException = "PROPOSITION-46"
    CarteBancaireRemboursementIbanNonCompleteException = "PROPOSITION-47"
    CarteBancaireRemboursementAutreFormatNonCompleteException = "PROPOSITION-48"
    ExperiencesAcademiquesNonCompleteesException = "PROPOSITION-49"
    TypeCompteBancaireRemboursementNonCompleteException = "PROPOSITION-50"
    CoordonneesNonCompleteesException = "PROPOSITION-51"


class DoctorateBusinessException(Enum):
    AbsenceDeDetteNonCompleteeDoctoratException = "DOCTORAT-1"
    ReductionDesDroitsInscriptionNonCompleteeDoctoratException = "DOCTORAT-2"
    AssimilationNonCompleteeDoctoratException = "DOCTORAT-3"
    AffiliationsNonCompleteesDoctoratException = "DOCTORAT-4"
    CarteBancaireRemboursementIbanNonCompleteDoctoratException = "DOCTORAT-5"
    CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException = "DOCTORAT-6"
    TypeCompteBancaireRemboursementNonCompleteDoctoratException = "DOCTORAT-7"


class GlobalPropositionBusinessException(Enum):
    BourseNonTrouveeException = "ADMISSION-1"
    ConditionsAccessNonRempliesException = "ADMISSION-2"
    QuestionsSpecifiquesChoixFormationNonCompleteesException = "ADMISSION-3"
    QuestionsSpecifiquesCurriculumNonCompleteesException = "ADMISSION-4"
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException = "ADMISSION-5"
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException = "ADMISSION-6"
    FormationNonTrouveeException = "ADMISSION-7"
    ReorientationInscriptionExterneNonConfirmeeException = "ADMISSION-8"
    ModificationInscriptionExterneNonConfirmeeException = "ADMISSION-9"
    PoolNonResidentContingenteNonOuvertException = "ADMISSION-10"
    ResidenceAuSensDuDecretNonRenseigneeException = "ADMISSION-11"
    AucunPoolCorrespondantException = "ADMISSION-12"
    PoolOuAnneeDifferentException = "ADMISSION-13"
    ElementsConfirmationNonConcordants = "ADMISSION-14"
    NombrePropositionsSoumisesDepasseException = "ADMISSION-15"
    PropositionNonTrouveeException = "ADMISSION-16"
    EmplacementDocumentNonTrouveException = "ADMISSION-17"
    DocumentsCompletesDifferentsDesReclamesException = "ADMISSION-18"
    PosteDiplomatiqueNonTrouveException = "ADMISSION-19"
    ResidenceAuSensDuDecretNonDisponiblePourInscriptionException = "ADMISSION-20"
    DocumentsReclamesImmediatementNonCompletesException = "ADMISSION-21"


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


BUSINESS_EXCEPTIONS_BY_TAB = {
    'project': {
        PropositionBusinessException.DetailProjetNonCompleteException,
    },
    'cotutelle': {
        PropositionBusinessException.CotutelleNonCompleteException,
    },
    'supervision': {
        PropositionBusinessException.ProcedureDemandeSignatureNonLanceeException,
        PropositionBusinessException.PropositionNonApprouveeParPromoteurException,
        PropositionBusinessException.PropositionNonApprouveeParMembresCAException,
        PropositionBusinessException.PromoteurManquantException,
        PropositionBusinessException.PromoteurDeReferenceManquantException,
        PropositionBusinessException.MembreCAManquantException,
        PropositionBusinessException.CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    },
    'confirmation-paper': set(),
    'extension-request': set(),
    'doctoral-training': set(),
    'complementary-training': set(),
    'course-enrollment': set(),
    'jury-preparation': set(),
    'jury': set(),
    'payment': set(),
}

TAB_OF_BUSINESS_EXCEPTION = {}
for tab in BUSINESS_EXCEPTIONS_BY_TAB:
    for exception in BUSINESS_EXCEPTIONS_BY_TAB[tab]:
        TAB_OF_BUSINESS_EXCEPTION[exception.value] = tab


class DoctorateCotutelleService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def update_cotutelle(cls, person, **kwargs):
        uuid = str(kwargs.pop('uuid'))
        return APIClient().update_cotutelle(
            uuid=uuid,
            definir_cotutelle_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_cotutelle(cls, person, uuid) -> CotutelleDTO:
        return APIClient().retrieve_cotutelle(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )


class DoctorateSupervisionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_admission_sdk.Configuration(
            host=settings.OSIS_ADMISSION_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.ADMISSION_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def get_supervision(cls, person, uuid) -> SupervisionDTO:
        return APIClient().retrieve_supervision(uuid=uuid, **build_mandatory_auth_headers(person))

    @classmethod
    def get_external_supervision(cls, uuid, token):
        return APIClient(api_config=cls.build_config()).get_external_proposition(
            uuid=uuid,
            token=token,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def get_signature_conditions(cls, person, uuid) -> SupervisionDTO:
        return APIClient().retrieve_verify_project(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def add_member(cls, person, uuid, **kwargs):
        return APIClient().add_member(
            uuid=uuid,
            identifier_supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def edit_external_member(cls, person, uuid, **kwargs):
        return APIClient().edit_external_member(
            uuid=uuid,
            modifier_membre_supervision_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_member(cls, person, uuid, **kwargs):
        return APIClient().remove_member(
            uuid=uuid,
            supervision_actor_reference=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def set_reference_promoter(cls, person, uuid, **kwargs):
        return APIClient().set_reference_promoter(
            uuid=uuid,
            designer_promoteur_reference_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def resend_invite(cls, person, uuid, **kwargs):
        return APIClient().update_signatures(
            uuid=uuid,
            renvoyer_invitation_signature_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_proposition(cls, person, uuid, **kwargs):
        return APIClient().approve_proposition(
            uuid=uuid,
            approuver_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def reject_proposition(cls, person, uuid, **kwargs):
        return APIClient().reject_proposition(
            uuid=uuid,
            refuser_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_external_proposition(cls, uuid, token, **kwargs):
        return APIClient(api_config=cls.build_config()).approve_external_proposition(
            uuid=uuid,
            token=token,
            approuver_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def reject_external_proposition(cls, uuid, token, **kwargs):
        return APIClient(api_config=cls.build_config()).reject_external_proposition(
            uuid=uuid,
            token=token,
            refuser_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def approve_by_pdf(cls, person, uuid, **kwargs):
        return APIClient().approve_by_pdf(
            uuid=uuid,
            approuver_proposition_par_pdf_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class DoctorateJuryService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_admission_sdk.Configuration(
            host=settings.OSIS_ADMISSION_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.ADMISSION_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def retrieve_jury(cls, person, uuid, **kwargs) -> JuryIdentityDTO:
        return APIClient().retrieve_jury_preparation(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def modifier_jury(cls, person, uuid, **kwargs) -> JuryIdentityDTO:
        return APIClient().update_jury_preparation(
            uuid=uuid,
            modifier_jury_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_jury_members(cls, person, uuid, **kwargs) -> List[MembreJuryIdentityDTO]:
        return APIClient().list_jury_members(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_jury_member(cls, person, uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().create_jury_members(
            uuid=uuid,
            ajouter_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().retrieve_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().remove_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().update_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            modifier_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_role_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().update_role_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            modifier_role_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )
