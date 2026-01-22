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
from django.utils.translation import gettext_lazy as _
from osis_parcours_doctoral_sdk.models.action_link import ActionLink

from parcours_doctoral.tests.mixins import BaseDoctorateTestCase


class ProjectDetailViewTestCase(BaseDoctorateTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:project', pk=cls.doctorate_uuid)

    def test_detail_no_permission(self):
        self.client.force_login(self.person.user)
        self.mock_doctorate_object.links['retrieve_project'] = ActionLink._from_openapi_data(error='access error')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_detail(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'osis-document.umd.min.js')
        self.assertContains(response, _('Proximity commission for experimental and clinical research (ECLI)'))
