# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ChoixStatutDoctorat(ChoiceEnum):
    # Creation in progress
    EN_ATTENTE_INJECTION_EPC = _('EN_ATTENTE_INJECTION_EPC')
    EN_COURS_DE_CREATION_PAR_GESTIONNAIRE = _('EN_COURS_DE_CREATION_PAR_GESTIONNAIRE')
    # After creation
    ADMIS = _('ADMIS')
    # Groupe de supervision
    EN_ATTENTE_DE_SIGNATURE = _('EN_ATTENTE_DE_SIGNATURE')
    # Confirmation paper
    CONFIRMATION_SOUMISE = _('CONFIRMATION_SOUMISE')
    CONFIRMATION_REUSSIE = _('CONFIRMATION_REUSSIE')
    NON_AUTORISE_A_POURSUIVRE = _('NON_AUTORISE_A_POURSUIVRE')
    CONFIRMATION_A_REPRESENTER = _('CONFIRMATION_A_REPRESENTER')
    # Jury
    JURY_SOUMIS = _('JURY_SOUMIS')
    JURY_APPROUVE_CA = _('JURY_APPROUVE_CA')
    JURY_APPROUVE_CDD = _('JURY_APPROUVE_CDD')
    JURY_REFUSE_CDD = _('JURY_REFUSE_CDD')
    JURY_APPROUVE_ADRE = _('JURY_APPROUVE_ADRE')
    JURY_REFUSE_ADRE = _('JURY_REFUSE_ADRE')
    # Recevabilité
    RECEVABILITE_SOUMISE = _('RECEVABILITE_SOUMISE')
    RECEVABILITE_A_RECOMMENCER = _('RECEVABILITE_A_RECOMMENCER')
    RECEVABILITE_REUSSIE = _('RECEVABILITE_REUSSIE')
    RECEVABILITE_EN_ECHEC = _('RECEVABILITE_EN_ECHEC')
    # Défense privée
    DEFENSE_PRIVEE_SOUMISE = _('DEFENSE_PRIVEE_SOUMISE')
    DEFENSE_PRIVEE_AUTORISEE = _('DEFENSE_PRIVEE_AUTORISEE')
    DEFENSE_PRIVEE_A_RECOMMENCER = _('DEFENSE_PRIVEE_A_RECOMMENCER')
    DEFENSE_PRIVEE_REUSSIE = _('DEFENSE_PRIVEE_REUSSIE')
    DEFENSE_PRIVEE_EN_ECHEC = _('DEFENSE_PRIVEE_EN_ECHEC')
    # Soutenance publique
    SOUTENANCE_PUBLIQUE_SOUMISE = _('SOUTENANCE_PUBLIQUE_SOUMISE')
    SOUTENANCE_PUBLIQUE_AUTORISEE = _('SOUTENANCE_PUBLIQUE_AUTORISEE')
    # Autres
    PROCLAME = _('PROCLAME')
    ABANDON = _('ABANDON')
