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

# Association between a read-only tab name (path name) and one or several action link keys
from django.utils.translation import gettext_lazy as _

READ_ACTIONS_BY_TAB = {
    # Project
    'project': 'retrieve_project',
    'cotutelle': 'retrieve_cotutelle',
    'funding': 'retrieve_funding',
    'supervision': 'retrieve_supervision',
    # Confirmation paper
    'confirmation-paper': 'retrieve_confirmation',
    'extension-request': 'update_confirmation_extension',
    # Jury
    'jury-preparation': 'retrieve_jury_preparation',
    'jury': 'list_jury_members',
    'jury_member': 'retrieve_jury_member',
    # Others
    'doctoral-training': 'retrieve_doctorate_training',
    'complementary-training': 'retrieve_complementary_training',
    'course-enrollment': 'retrieve_course_enrollment',
    'assessment-enrollment': 'retrieve_assessment_enrollment',
    'private-defense': 'retrieve_private_defense',
    'public-defense': '',
    'messages': '',
}

# Association between a write-only tab name (path name) and one or several action link keys
UPDATE_ACTIONS_BY_TAB = {
    # Project
    'cotutelle': 'update_cotutelle',
    'supervision': 'request_signatures',
    'funding': 'update_funding',
    # Confirmation paper
    'confirmation-paper': ['update_confirmation', 'upload_pdf_confirmation'],
    'extension-request': 'update_confirmation_extension',
    # Jury
    'jury-preparation': 'update_jury_preparation',
    'jury': 'create_jury_members',
    'jury_member': 'update_jury_member',
    # Others
    'doctoral-training': 'retrieve_doctorate_training',
    'complementary-training': 'retrieve_complementary_training',
    'course-enrollment': 'retrieve_course_enrollment',
    'assessment-enrollment': 'retrieve_assessment_enrollment',
    'private-defense': 'update_private_defense',
    'public-defense': '',
    'messages': '',
}

UCL_CODE = 'UCL'

BE_ISO_CODE = 'BE'

FIELD_REQUIRED_MESSAGE = _("This field is required.")

FIRST_YEAR_WITH_ECTS_BE = 2004

LINGUISTIC_REGIMES_WITHOUT_TRANSLATION = ['FR', 'NL', 'DE', 'EN', 'IT', 'ES', 'PT']

MINIMUM_YEAR = 1900

MINIMUM_BIRTH_YEAR = 1920

PLUS_5_ISO_CODES = [
    'CH',  # Switzerland
    'IS',  # Island
    'NO',  # Norway
    'LI',  # Liechtenstein
    'MC',  # Monaco
]
