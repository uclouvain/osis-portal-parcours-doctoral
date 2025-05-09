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
from django.utils.translation import pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class StatutActivite(ChoiceEnum):
    NON_SOUMISE = _("NON_SOUMISE")
    SOUMISE = _("SOUMISE")
    ACCEPTEE = _("ACCEPTEE")
    REFUSEE = _("REFUSEE")


class CategorieActivite(ChoiceEnum):
    CONFERENCE = _("CONFERENCE")
    COMMUNICATION = _("COMMUNICATION")
    SEMINAR = _("SEMINAR")
    PUBLICATION = _("PUBLICATION")
    SERVICE = _("SERVICE")
    RESIDENCY = _("RESIDENCY")
    VAE = _("VAE")
    COURSE = _("COURSE")
    PAPER = _("PAPER")
    UCL_COURSE = _("UCL_COURSE")


class ChoixComiteSelection(ChoiceEnum):
    YES = _("YES")
    NO = _("NO")
    NA = _("N/A")


class ChoixStatutPublication(ChoiceEnum):
    UNSUBMITTED = pgettext_lazy("publication-status", "Unsubmitted")
    SUBMITTED = pgettext_lazy("publication-status", "Submitted")
    IN_REVIEW = pgettext_lazy("publication-status", "Awaiting approval")
    DEPOSITED = pgettext_lazy("publication-status", "Deposited")
    ACCEPTED = pgettext_lazy("publication-status", "Accepted")
    PUBLISHED = pgettext_lazy("publication-status", "Published")


class ChoixTypeVolume(ChoiceEnum):
    HEURES = _("hours")
    JOURS = _("days")


class ChoixRolePublication(ChoiceEnum):
    AUTERTRICE_UNIQUE = _("Only author")
    COAUTEURTRICE = _("Co-author")
    PREMIER_AUTEURTRICE = _("First author")
    DEUXIEME_AUTEURTRICE = _("Second author")
    EDITEURTRICE = _("Editor")
    COEDITEURTRICE = _("Co-editor")


class ChoixTypeEpreuve(ChoiceEnum):
    CONFIRMATION_PAPER = _("CONFIRMATION_PAPER")
    PRIVATE_DEFENSE = _("PRIVATE_DEFENSE")
    PUBLIC_DEFENSE = _("PUBLIC_DEFENSE")


class ContexteFormation(ChoiceEnum):
    DOCTORAL_TRAINING = _("DOCTORAL_TRAINING")
    COMPLEMENTARY_TRAINING = _("COMPLEMENTARY_TRAINING")


class Session(ChoiceEnum):
    JANUARY = pgettext_lazy("session", "January")
    JUNE = pgettext_lazy("session", "June")
    SEPTEMBER = pgettext_lazy("session", "September")


class StatutInscriptionEvaluation(ChoiceEnum):
    ACCEPTEE = _("ACCEPTEE")
    DESINSCRITE = _("DESINSCRITE")
