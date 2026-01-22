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

from unittest.mock import Mock, patch

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext
from django.views.generic import FormView
from osis_parcours_doctoral_sdk.exceptions import UnauthorizedException
from osis_parcours_doctoral_sdk.models.action_link import ActionLink
from osis_parcours_doctoral_sdk.models.parcours_doctoral_dto_links import (
    ParcoursDoctoralDTOLinks,
)

from base.models.utils.utils import ChoiceEnum
from base.tests.factories.person import PersonFactory
from parcours_doctoral.contrib.forms import PDF_MIME_TYPE, DoctorateFileUploadField
from parcours_doctoral.templatetags.parcours_doctoral import (
    TAB_TREE,
    Tab,
    can_make_action,
    can_read_tab,
    can_update_tab,
    display,
    form_fields_are_empty,
    get_valid_tab_tree,
    strip,
    value_if_all,
    value_if_any,
)


class TemplateTagsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        class Doctorate:
            def __init__(self, links=None):
                self.links = links or {
                    'retrieve_funding': {'url': 'my_url', 'method': 'GET'},
                    'update_funding': {'url': 'my_url', 'method': 'POST'},
                    'retrieve_project': {'error': 'Method not allowed', 'method': 'GET'},
                }

        cls.Doctorate = Doctorate

    def test_normal_panel(self):
        template = Template("{% load parcours_doctoral %}{% panel 'Coucou' %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertIn('<h4 class="card-title">', rendered)
        self.assertIn('Coucou', rendered)
        self.assertIn('<div class="card-body">', rendered)

    def test_panel_no_title(self):
        template = Template("{% load parcours_doctoral %}{% panel %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertNotIn('<h4 class="card-title">', rendered)
        self.assertIn('<div class="card-body">', rendered)

    def test_enum_value(self):
        class TestEnum(ChoiceEnum):
            FOO = "Bar"

        template = Template("{% load enums %}{{ value|enum_display:'TestEnum' }}")
        rendered = template.render(Context({'value': "TEST"}))
        self.assertEqual('TEST', rendered)

        rendered = template.render(Context({'value': ""}))
        self.assertEqual('', rendered)

        rendered = template.render(Context({'value': None}))
        self.assertEqual('None', rendered)

        obj = Mock()
        obj.__str__ = lambda _: "obj"
        rendered = template.render(Context({'value': obj}))
        self.assertEqual('obj', rendered)

        rendered = template.render(Context({'value': "FOO"}))
        self.assertEqual('Bar', rendered)

        template = Template("{% load enums %}{{ value|enum_display:'InexistantEnum' }}")
        rendered = template.render(Context({'value': "TEST"}))
        self.assertEqual('TEST', rendered)

    def test_multiple_enum_display(self):
        class MultipleTestEnum(ChoiceEnum):
            A = "TEST A"
            B = "TEST B"
            C = "TEST C"

        template = Template("{% load enums %}{{ values|multiple_enum_display:'MultipleTestEnum' }}")

        # Empty list
        rendered = template.render(Context({'values': []}))
        self.assertEqual('', rendered)

        # One unknown value
        rendered = template.render(Context({'values': ["FOO"]}))
        self.assertEqual('FOO', rendered)

        # Multiple unknown values
        rendered = template.render(Context({'values': ["FOO", "BAR"]}))
        self.assertEqual('FOO, BAR', rendered)

        # One known value
        rendered = template.render(Context({'values': ["A"]}))
        self.assertEqual('TEST A', rendered)

        # Multiple known values
        rendered = template.render(Context({'values': ["A", "B"]}))
        self.assertEqual('TEST A, TEST B', rendered)

    def test_tabs(self):
        doctorate_uuid = '55375049-9d61-4c11-9f41-7460463a5ae3'

        class MockedFormView(FormView):
            def __new__(cls, *args, **kwargs):
                return Mock(
                    kwargs={
                        'pk': doctorate_uuid,
                    },
                    spec=cls,
                )

        project_tab_url = f'/parcours_doctoral/{doctorate_uuid}/project'
        template = Template("{% load parcours_doctoral %}{% doctorate_tabs doctorate %}")
        doctorate = Mock(
            uuid=doctorate_uuid,
            links=ParcoursDoctoralDTOLinks(
                retrieve_project=ActionLink._from_openapi_data(method='GET', url='ok'),
            ),
        )

        request = RequestFactory().get(project_tab_url)
        request.resolver_match = resolve(project_tab_url)
        rendered = template.render(Context({'view': MockedFormView(), 'request': request, 'doctorate': doctorate}))
        self.assertNotIn('confirm-paper', rendered)
        self.assertIn(project_tab_url, rendered)
        self.assertInHTML(
            """
            <li role="presentation" class="nav-item">
                <a
                    href="/parcours_doctoral/55375049-9d61-4c11-9f41-7460463a5ae3/project"
                    aria-current="page"
                    class="nav-link active"
                    >
                    <span class="fa fa-person-chalkboard"></span>
                    Recherche
                </a>
            </li>
            """,
            rendered,
        )

        # Should work on non-tab urls
        another_tab_url = '/parcours_doctoral/list'
        request = RequestFactory().get(another_tab_url)
        request.resolver_match = resolve(another_tab_url)
        rendered = template.render(Context({'view': MockedFormView(), 'request': request, 'doctorate': doctorate}))
        self.assertIn(project_tab_url, rendered)
        self.assertInHTML(
            """
            <li role="presentation" class="nav-item">
                <a href="/parcours_doctoral/55375049-9d61-4c11-9f41-7460463a5ae3/project" class="nav-link">
                    <span class="fa fa-person-chalkboard"></span>
                    Recherche
                </a>
            </li>
            """,
            rendered,
        )

    def test_field_data(self):
        template = Template("{% load parcours_doctoral %}{% field_data 'title' data 'col-md-12' %}")
        rendered = template.render(Context({'data': "content"}))
        self.assertIn('content', rendered)
        self.assertIn('title', rendered)
        self.assertIn('<dd>', rendered)
        self.assertIn('class="col-md-12"', rendered)

    def test_field_data_translated(self):
        template = Template("{% load parcours_doctoral %}{% field_data 'title' data translate_data=True %}")
        rendered = template.render(Context({'data': "Personal data"}))
        self.assertIn(str(_('Personal data')), rendered)

    @patch('osis_document_components.services.get_remote_token', return_value='foobar')
    @patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'size': 1,
        },
    )
    def test_field_data_with_list(self, *args):
        template = Template("{% load parcours_doctoral %}{% field_data 'title' data %}")
        rendered = template.render(Context({'data': ['55375049-9d61-4c11-9f41-7460463a5ae3']}))
        self.assertIn('document-visualizer', rendered)
        self.assertNotIn('55375049-9d61-4c11-9f41-7460463a5ae3', rendered)
        self.assertIn('foobar', rendered)

    def test_valid_tab_tree_no_doctorate(self):
        # No doctorate is specified -> return the original tab tree
        valid_tab_tree = get_valid_tab_tree(TAB_TREE, doctorate=None)
        self.assertEqual(valid_tab_tree, TAB_TREE)

    def test_valid_tab_tree_read_mode(self):
        # Only one read tab is allowed -> return it and its parent

        doctorate = self.Doctorate()

        valid_tab_tree = get_valid_tab_tree(TAB_TREE, doctorate)

        parent_tabs = list(valid_tab_tree.keys())

        # Check parent tabs
        self.assertEqual(len(parent_tabs), 1)
        self.assertEqual(parent_tabs[0].label, pgettext('tab name', 'Research'))

        # Check children tabs
        self.assertIn('funding', valid_tab_tree[parent_tabs[0]])

    def test_valid_tab_tree_update_mode(self):
        # Only one form tab is allowed -> return it and its parent

        doctorate = self.Doctorate()
        valid_tab_tree = get_valid_tab_tree(TAB_TREE, doctorate)

        parent_tabs = list(valid_tab_tree.keys())

        # Check parent tabs
        self.assertEqual(len(parent_tabs), 1)
        self.assertEqual(parent_tabs[0].label, pgettext('tab name', 'Research'))

        # Check children tabs
        self.assertIn('funding', valid_tab_tree[parent_tabs[0]])

    def test_can_make_action_valid_existing_action(self):
        # The tab action is specified in the doctorate as allowed -> return True
        doctorate = self.Doctorate()
        self.assertTrue(can_make_action(doctorate, 'retrieve_funding'))

    def test_can_make_action_invalid_existing_action(self):
        # The tab action is specified in the doctorate as not allowed -> return False
        doctorate = self.Doctorate()
        self.assertFalse(can_make_action(doctorate, 'retrieve_project'))

    def test_can_make_action_not_returned_action(self):
        # The tab action is not specified in the doctorate -> return False
        doctorate = self.Doctorate()
        self.assertFalse(can_make_action(doctorate, 'unknown'))

    def test_can_read_tab_valid_existing_tab(self):
        # The tab action is specified in the doctorate as allowed -> return True
        doctorate = self.Doctorate()
        self.assertTrue(can_read_tab(doctorate, Tab('funding', '')))

    def test_can_read_tab_invalid_existing_tab(self):
        # The tab action is well configured as not allowed -> return False
        doctorate = self.Doctorate()
        self.assertFalse(can_read_tab(doctorate, Tab('project', '')))

    def test_can_read_tab_not_returned_action(self):
        # The tab action is not specified in the doctorate -> return False
        doctorate = self.Doctorate()
        self.assertFalse(can_read_tab(doctorate, Tab('project', '')))

    def test_can_read_tab_unknown_tab(self):
        # The tab action is unknown -> raise an exception
        doctorate = self.Doctorate()
        with self.assertRaisesMessage(ImproperlyConfigured, 'unknown'):
            can_read_tab(doctorate, Tab('unknown', ''))

    def test_can_read_tab_no_doctorate_links(self):
        # The tab action is unknown -> raise an exception
        doctorate = self.Doctorate()
        delattr(doctorate, 'links')
        with self.assertRaisesMessage(ImproperlyConfigured, 'links'):
            can_read_tab(doctorate, Tab('funding', ''))

    def test_can_update_tab_valid_existing_action(self):
        # The tab action is specified in the doctorate as allowed -> return True
        doctorate = self.Doctorate()
        self.assertTrue(can_update_tab(doctorate, Tab('funding', '')))

    def test_get_dashboard_links_tag(self):
        template = Template(
            """{% load parcours_doctoral %}{% get_dashboard_links %}
            {% if 'url' in links.list_doctorates %}coucou{% endif %}"""
        )
        with patch('parcours_doctoral.services.doctorate.DoctorateService') as mock_api:
            mock_api.side_effect = UnauthorizedException
            request = RequestFactory()
            request.user = PersonFactory().user
            rendered = template.render(Context({'request': request}))
        self.assertNotIn('coucou', rendered)


class DisplayTagTestCase(TestCase):
    class TestForm(forms.Form):
        boolean_field = forms.BooleanField()
        char_field = forms.CharField()
        integer_field = forms.IntegerField()
        float_field = forms.FloatField()
        file_field = DoctorateFileUploadField()

    def test_comma(self):
        self.assertEqual(display('', ',', None), '')
        self.assertEqual(display('', ',', 0), '')
        self.assertEqual(display('', ',', ''), '')
        self.assertEqual(display('Foo', ',', []), 'Foo')
        self.assertEqual(display('', ',', "bar"), 'bar')
        self.assertEqual(display('foo', '-', "", '-', ''), 'foo')
        self.assertEqual(display('foo', '-', "bar", '-', ''), 'foo - bar')
        self.assertEqual(display('foo', '-', None, '-', ''), 'foo')
        self.assertEqual(display('foo', '-', None, '-', 'baz'), 'foo - baz')
        self.assertEqual(display('foo', '-', "bar", '-', 'baz'), 'foo - bar - baz')
        self.assertEqual(display('-'), '')
        self.assertEqual(display('', '-', ''), '')
        self.assertEqual(display('-', '-'), '-')
        self.assertEqual(display('-', '-', '-'), '-')

    def test_parenthesis(self):
        self.assertEqual(display('(', '', ")"), '')
        self.assertEqual(display('(', None, ")"), '')
        self.assertEqual(display('(', 0, ")"), '')
        self.assertEqual(display('(', 'lol', ")"), '(lol)')

    def test_suffix(self):
        self.assertEqual(display('', ' grammes'), '')
        self.assertEqual(display(5, ' grammes'), '5 grammes')
        self.assertEqual(display(5, ' grammes'), '5 grammes')
        self.assertEqual(display(0.0, ' g'), '')

    def test_both(self):
        self.assertEqual(display('(', '', ")", '-', 0), '')
        self.assertEqual(display('(', '', ",", "", ")", '-', 0), '')
        self.assertEqual(display('(', 'jean', ",", "", ")", '-', 0), '(jean)')
        self.assertEqual(display('(', 'jean', ",", "michel", ")", '-', 0), '(jean, michel)')
        self.assertEqual(display('(', 'jean', ",", "michel", ")", '-', 100), '(jean, michel) - 100')

    def test_strip(self):
        self.assertEqual(strip(' coucou '), 'coucou')
        self.assertEqual(strip(0), 0)
        self.assertEqual(strip(None), None)

    def test_value_if_all(self):
        self.assertEqual(value_if_all('value'), 'value')
        self.assertEqual(value_if_all('value', True), 'value')
        self.assertEqual(value_if_all('value', False), '')
        self.assertEqual(value_if_all('value', None), '')
        self.assertEqual(value_if_all('value', True, True, False), '')

    def test_value_if_any(self):
        self.assertEqual(value_if_any('value'), '')
        self.assertEqual(value_if_any('value', True), 'value')
        self.assertEqual(value_if_any('value', False), '')
        self.assertEqual(value_if_any('value', None), '')
        self.assertEqual(value_if_any('value', True, False, False), 'value')
        self.assertEqual(value_if_any('value', False, False, False), '')

    def test_form_fields_are_empty(self):
        # Initial values that are not empty and truthy
        values = {
            'boolean_field': True,
            'char_field': 'foo',
            'integer_field': 42,
            'float_field': 3.14,
            'file_field': ['tmp'],
        }
        form = self.TestForm(initial=values)
        self.assertFalse(form_fields_are_empty(form, 'boolean_field'))
        self.assertFalse(form_fields_are_empty(form, 'char_field'))
        self.assertFalse(form_fields_are_empty(form, 'integer_field'))
        self.assertFalse(form_fields_are_empty(form, 'float_field'))
        self.assertFalse(form_fields_are_empty(form, 'file_field'))

        # Submitted values that are not empty but eventually falsy
        values = {
            'boolean_field': False,
            'char_field': 'foo',
            'integer_field': 0,
            'float_field': 0.0,
            'file_field': ['tmp'],
        }

        form = self.TestForm(data=values)

        self.assertFalse(form_fields_are_empty(form, 'boolean_field'))
        self.assertFalse(form_fields_are_empty(form, 'char_field'))
        self.assertFalse(form_fields_are_empty(form, 'integer_field'))
        self.assertFalse(form_fields_are_empty(form, 'float_field'))
        self.assertFalse(form_fields_are_empty(form, 'file_field'))

        # No submitted values
        form = self.TestForm()

        self.assertTrue(form_fields_are_empty(form, 'boolean_field'))
        self.assertTrue(form_fields_are_empty(form, 'char_field'))
        self.assertTrue(form_fields_are_empty(form, 'integer_field'))
        self.assertTrue(form_fields_are_empty(form, 'float_field'))
        self.assertTrue(form_fields_are_empty(form, 'file_field'))

        # Submitted values that are empty
        values = {
            'boolean_field': None,
            'char_field': '',
            'integer_field': None,
            'float_field': None,
            'file_field': [],
        }

        form = self.TestForm(initial=values)

        self.assertTrue(form_fields_are_empty(form, 'boolean_field'))
        self.assertTrue(form_fields_are_empty(form, 'char_field'))
        self.assertTrue(form_fields_are_empty(form, 'integer_field'))
        self.assertTrue(form_fields_are_empty(form, 'float_field'))
        self.assertTrue(form_fields_are_empty(form, 'file_field'))

        self.assertTrue(
            form_fields_are_empty(form, 'boolean_field', 'char_field', 'integer_field', 'float_field', 'file_field'),
        )
