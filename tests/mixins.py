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
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

from django.test import override_settings
from osis_parcours_doctoral_sdk.model.action_link import ActionLink
from osis_parcours_doctoral_sdk.model.cotutelle_dto_nested import CotutelleDTONested
from osis_parcours_doctoral_sdk.model.entite_gestion_dto_nested import (
    EntiteGestionDTONested,
)
from osis_parcours_doctoral_sdk.model.financement_dto_nested import FinancementDTONested
from osis_parcours_doctoral_sdk.model.formation_dto_nested import FormationDTONested
from osis_parcours_doctoral_sdk.model.jury_dto import JuryDTO
from osis_parcours_doctoral_sdk.model.membre_jury_dto_nested import MembreJuryDTONested
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto import ParcoursDoctoralDTO
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto_links import (
    ParcoursDoctoralDTOLinks,
)
from osis_parcours_doctoral_sdk.model.projet_dto_nested import ProjetDTONested
from osis_parcours_doctoral_sdk.model.signature_membre_jury_dto_nested import (
    SignatureMembreJuryDTONested,
)
from osis_reference_sdk.model.language import Language
from osis_reference_sdk.model.scholarship import Scholarship

from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase
from parcours_doctoral.contrib.enums import (
    AdmissionType,
    ChoixLangueDefense,
    ChoixStatutDoctorat,
    TypeBourse,
)
from parcours_doctoral.contrib.enums.financement import (
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from parcours_doctoral.contrib.enums.proximity_commission import (
    ChoixCommissionProximiteCDSS,
)
from parcours_doctoral.contrib.forms import PDF_MIME_TYPE


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    PARCOURS_DOCTORAL_TOKEN_EXTERNAL='api-token-external',
)
class BaseDoctorateTestCase(OsisPortalTestCase):
    mime_type = PDF_MIME_TYPE

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()
        cls.doctorate_uuid = str(uuid4())
        cls.scholarship_uuid = str(uuid4())
        cls.api_default_params = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def _mock_doctorate_api(self):
        doctorate_api_patcher = patch('osis_parcours_doctoral_sdk.api.doctorate_api.DoctorateApi')
        self.mock_doctorate_api = doctorate_api_patcher.start()
        self.addCleanup(doctorate_api_patcher.stop)

        self.mock_doctorate_object = ParcoursDoctoralDTO._from_openapi_data(
            uuid=self.doctorate_uuid,
            reference='L-CDAR24-0000-0002',
            statut=ChoixStatutDoctorat.ADMIS.name,
            date_changement_statut=datetime.datetime(2024, 1, 3),
            cree_le=datetime.datetime(2024, 1, 1),
            archive=[],
            uuid_admission=str(uuid.uuid4()),
            type_admission=AdmissionType.ADMISSION.name,
            intitule_secteur_formation='First sector',
            sigle_entite_gestion='SSH',
            formation=FormationDTONested._from_openapi_data(
                sigle='SC3DP',
                code='DKOE',
                annee=2024,
                intitule='Doctorate',
                intitule_fr='Doctorat',
                intitule_en='Doctorate',
                entite_gestion=EntiteGestionDTONested._from_openapi_data(
                    sigle='CDAR',
                    intitule='First commission',
                    lieu='Place de l\'université',
                    ville='Louvain-La-Neuve',
                    code_postal='1348',
                    pays='BE',
                    numero_telephone='',
                    code_secteur='S1',
                    intitule_secteur='First sector',
                    nom_pays='Belgique',
                ),
                campus=dict(
                    uuid='',
                    nom='Louvain-La-Neuve',
                    code_postal='1348',
                    ville='Louvain-La-Neuve',
                    pays_iso_code='BE',
                    nom_pays='Belgium',
                    rue='Place de l\'université',
                    numero_rue='1',
                    boite_postale='B1',
                    localisation='L1',
                ),
                type='PHD',
            ),
            projet=ProjetDTONested._from_openapi_data(
                titre='Title',
                resume='Summary',
                langue_redaction_these='FR-BE',
                nom_langue_redaction_these='French',
                institut_these=str(uuid4()),
                nom_institut_these='Institute',
                sigle_institut_these='I1',
                lieu_these='Louvain-La-Neuve',
                projet_doctoral_deja_commence=True,
                projet_doctoral_institution='Institute 2',
                projet_doctoral_date_debut=datetime.date(2023, 1, 1),
                documents_projet=[],
                graphe_gantt=[],
                proposition_programme_doctoral=[],
                projet_formation_complementaire=[],
                lettres_recommandation=[],
                doctorat_deja_realise='YES',
                institution='Institute 3',
                domaine_these='D1',
                date_soutenance=datetime.date(2024, 1, 1),
                raison_non_soutenue='Reason',
            ),
            code_secteur_formation='SSH',
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            date_naissance_doctorant=datetime.date(2000, 1, 1),
            lieu_naissance_doctorant='Bruxelles',
            pays_naissance_doctorant='Belgique',
            links=ParcoursDoctoralDTOLinks._from_openapi_data(
                **{
                    action: ActionLink._from_openapi_data(
                        url='ok',
                        error='',
                        method='GET',
                    )
                    for action in [
                        'retrieve_project',
                        'retrieve_cotutelle',
                        'update_cotutelle',
                        'retrieve_funding',
                        'update_funding',
                        'retrieve_supervision',
                        'retrieve_supervision_canvas',
                        'retrieve_confirmation',
                        'update_confirmation',
                        'update_confirmation_extension',
                        'retrieve_doctorate_training',
                        'retrieve_complementary_training',
                        'retrieve_course_enrollment',
                        'retrieve_assessment_enrollment',
                        'retrieve_private_defense',
                        'retrieve_private_defense_minutes_canvas',
                        'retrieve_public_defense',
                        'update_private_defense',
                        'submit_private_defense_minutes',
                        'update_public_defense',
                        'add_training',
                        'submit_training',
                        'assent_training',
                        'retrieve_jury_preparation',
                        'update_jury_preparation',
                        'list_jury_members',
                        'create_jury_members',
                        'upload_pdf_confirmation',
                        'jury_request_signatures',
                    ]
                }
            ),
            cotutelle=CotutelleDTONested._from_openapi_data(
                cotutelle=True,
                motivation='Cotutelle reason',
                institution_fwb=True,
                institution=str(uuid4()),
                autre_institution=True,
                autre_institution_nom='Cotutelle institution',
                autre_institution_adresse='Mons',
                demande_ouverture=[],
                convention=[],
                autres_documents=[],
            ),
            financement=FinancementDTONested._from_openapi_data(
                type=ChoixTypeFinancement.WORK_CONTRACT.name,
                type_contrat_travail=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                eft=10,
                bourse_recherche=dict(
                    uuid=self.scholarship_uuid,
                    nom_long='DS1',
                    nom_court='Doctorate scholarship 1',
                    type=TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
                ),
                autre_bourse_recherche='Other scholarship',
                bourse_date_debut=datetime.date(2022, 1, 1),
                bourse_date_fin=datetime.date(2025, 1, 1),
                bourse_preuve=[],
                duree_prevue=10,
                temps_consacre=20,
                est_lie_fnrs_fria_fresh_csc=True,
                commentaire='Comment',
            ),
            photo_identite_doctorant=[],
            matricule_doctorant=self.person.global_id,
            noma_doctorant='0202020202',
            genre_doctorant='H',
            prenom_doctorant='John',
            nom_doctorant='Doe',
            commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name,
            justification='Justification',
            titre_these_propose='Title',
            langue_soutenance_publique=ChoixLangueDefense.FRENCH.name,
            autre_langue_soutenance_publique='Japanese',
            date_heure_soutenance_publique=datetime.datetime(2024, 2, 2, 11, 30),
            lieu_soutenance_publique='Louvain-La-Neuve',
            local_deliberation='D1',
            informations_complementaires_soutenance_publique='Information',
            resume_annonce='Announcement summary',
            photo_annonce=[],
            proces_verbal_soutenance_publique=[],
            date_retrait_diplome=datetime.date(2025, 2, 2),
        )
        self.mock_doctorate_api.return_value.doctorate_retrieve.return_value = self.mock_doctorate_object
        self.mock_doctorate_api.return_value.retrieve_jury_preparation.return_value = JuryDTO._from_openapi_data(
            uuid=self.doctorate_uuid,
            titre_propose='titre propose',
            has_change_roles_permission=True,
            membres=[
                MembreJuryDTONested(
                    uuid='7695d217-0a52-46fc-b4a8-3892621025e9',
                    role='MEMBRE',
                    est_promoteur=True,
                    est_promoteur_de_reference=True,
                    matricule='0123456789',
                    institution='',
                    autre_institution='',
                    pays='pays',
                    nom='Troufignon',
                    prenom='prenom',
                    titre='titre',
                    justification_non_docteur='',
                    genre='F',
                    langue='FR',
                    email='email@example.org',
                    signature=SignatureMembreJuryDTONested(
                        etat='APPROVED',
                        commentaire_externe="A public comment to display",
                        commentaire_interne='',
                        motif_refus='',
                        pdf=[],
                    ),
                ),
                MembreJuryDTONested(
                    uuid='74ca8fbf-4566-437c-b6bb-c0c4780ec046',
                    role='MEMBRE',
                    est_promoteur=True,
                    est_promoteur_de_reference=False,
                    matricule=self.person.global_id,
                    institution='',
                    autre_institution='',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='titre',
                    justification_non_docteur='',
                    genre='F',
                    langue='FR',
                    email='email@example.org',
                    signature=SignatureMembreJuryDTONested(
                        etat='INVITED',
                        commentaire_externe="",
                        commentaire_interne='',
                        motif_refus='',
                        pdf=[],
                    ),
                ),
            ],
            formule_defense='',
            date_indicative='2025-08-01',
            nom_langue_redaction='',
            langue_redaction='',
            nom_langue_soutenance='',
            langue_soutenance='',
            commentaire='',
            approbation_pdf=[],
            situation_comptable=None,
        )

    def _mock_document_api(self):
        document_api_patcher = patch('osis_document_components.services.get_remote_token', return_value='foobar')
        document_api_patcher.start()
        self.addCleanup(document_api_patcher.stop)

        document_api_patcher = patch(
            'osis_document_components.services.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': self.mime_type, 'size': 1},
        )
        document_api_patcher.start()

    def _mock_reference_api(self):
        language_patcher = patch('osis_reference_sdk.api.languages_api.LanguagesApi')
        self.mock_language_api = language_patcher.start()
        self.addCleanup(language_patcher.stop)

        self.mock_language_api.return_value.languages_list.return_value = MagicMock(
            results=[
                Language._from_openapi_data(
                    code='FR',
                    name='Français',
                    name_en='French',
                ),
            ],
        )

        superior_institute_patcher = patch('osis_reference_sdk.api.universities_api.UniversitiesApi')
        self.mock_superior_institute_api = superior_institute_patcher.start()
        self.addCleanup(superior_institute_patcher.stop)

        self.mock_superior_institute_api.return_value.university_read.return_value = MagicMock(
            uuid='foo',
            name='foo',
            street='foo',
            street_number='foo',
            zipcode='foo',
            city='foo',
        )

        scholarship_patcher = patch('osis_reference_sdk.api.scholarship_api.ScholarshipApi')
        self.mock_scholarship_api = scholarship_patcher.start()
        self.addCleanup(scholarship_patcher.stop)

        self.mock_scholarship_object = Scholarship._from_openapi_data(
            uuid=self.scholarship_uuid,
            short_name='DS1',
            long_name='Doctorate Scholarship 1',
            type=TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
        )
        self.mock_scholarship_api.return_value.retrieve_scholarship.return_value = self.mock_scholarship_object

    def setUp(self):
        super().setUp()

        self._mock_doctorate_api()
        self._mock_document_api()
        self._mock_reference_api()
