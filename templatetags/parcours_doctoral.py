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

import functools
import re
from contextlib import suppress
from dataclasses import dataclass
from inspect import getfullargspec
from typing import Union

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import EMPTY_VALUES
from django.utils.safestring import SafeString
from django.utils.translation import get_language, gettext_lazy as _, pgettext, pgettext_lazy

from osis_admission_sdk.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from osis_admission_sdk.model.supervision_dto_promoteur import SupervisionDTOPromoteur
from parcours_doctoral.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from parcours_doctoral.contrib.enums.training import CategorieActivite, ChoixTypeEpreuve, StatutActivite
from parcours_doctoral.contrib.forms.supervision import DoctorateMemberSupervisionForm
from parcours_doctoral.services.reference import CountriesService
from parcours_doctoral.utils import to_snake_case, format_academic_year

register = template.Library()


class PanelNode(template.library.InclusionNode):
    def __init__(self, nodelist: dict, func, takes_context, args, kwargs, filename):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist_dict = nodelist

    def render(self, context):
        for context_name, nodelist in self.nodelist_dict.items():
            context[context_name] = nodelist.render(context)
        return super().render(context)


def register_panel(filename, takes_context=None, name=None):
    def dec(func):
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        function_name = name or getattr(func, '_decorated_function', func).__name__

        @functools.wraps(func)
        def compile_func(parser, token):
            # {% panel %} and its arguments
            bits = token.split_contents()[1:]
            args, kwargs = template.library.parse_bits(
                parser, bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults, takes_context, function_name
            )
            nodelist_dict = {'panel_body': parser.parse(('footer', 'endpanel'))}
            token = parser.next_token()

            # {% footer %} (optional)
            if token.contents == 'footer':
                nodelist_dict['panel_footer'] = parser.parse(('endpanel',))
                parser.next_token()

            return PanelNode(nodelist_dict, func, takes_context, args, kwargs, filename)

        register.tag(function_name, compile_func)
        return func

    return dec


@dataclass(frozen=True)
class Tab:
    name: str
    label: str
    icon: str = ''

    def __eq__(self, o) -> bool:
        if isinstance(o, Tab):
            return o.name == self.name
        return o == self.name

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)

    def __str__(self):
        return self.name


TAB_TREES = {
    'doctorate': {
        Tab('doctorate', pgettext('tab name', 'Research project'), 'person-chalkboard'): [
            Tab('project', pgettext('tab name', 'Research project')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Support committee')),
        ],
        Tab('confirmation-paper', _('Confirmation'), 'list-check'): [
            Tab('confirmation-paper', _('Confirmation exam')),
            Tab('extension-request', _('New deadline')),
        ],
        Tab('training', pgettext_lazy('doctorate', 'Course'), 'book-open-reader'): [
            Tab('doctoral-training', _('PhD training')),
            Tab('complementary-training', _('Complementary training')),
            Tab('course-enrollment', _('Course unit enrolment')),
        ],
        Tab('defense', pgettext('doctorate tab', 'Defense'), 'person-chalkboard'): [
            Tab('jury-preparation', pgettext('doctorate tab', 'Defense method')),
            Tab('jury', _('Jury composition')),
            # Tab('jury-supervision', _('Jury supervision')),
            # Tab('private-defense', _('Private defense')),
            # Tab('public-defense', _('Public defense')),
        ],
    },
}


def _get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


@register.filter
def can_make_action(doctorate, action_name):
    """Return true if the specified action can be applied for this doctorate, otherwise return False"""
    if not doctorate:
        return False
    return 'url' in doctorate.links.get(action_name, {})


def _can_access_tab(doctorate, tab_name, actions_by_tab):
    """Return true if the specified tab can be opened for this doctorate, otherwise return False"""
    try:
        return can_make_action(doctorate, actions_by_tab[tab_name])
    except AttributeError:
        raise ImproperlyConfigured("The doctorate should contain the 'links' property to check tab access")
    except KeyError:
        raise ImproperlyConfigured(
            "Please check that the '{}' property is well specified in the 'READ_ACTIONS_BY_TAB' and"
            " 'UPDATE_ACTIONS_BY_TAB' constants".format(tab_name)
        )


def get_valid_tab_tree(tab_tree, doctorate):
    """
    Return a tab tree based on the specified one but whose tabs depending on the permissions links.
    """
    if doctorate:
        valid_tab_tree = {}

        # Loop over the tabs of the original tab tree
        for parent_tab, sub_tabs in tab_tree.items():
            # Get the accessible sub tabs depending on the user permissions
            valid_sub_tabs = [tab for tab in sub_tabs if _can_access_tab(doctorate, tab.name, READ_ACTIONS_BY_TAB)]
            # Only add the parent tab if at least one sub tab is allowed
            if len(valid_sub_tabs) > 0:
                valid_tab_tree[parent_tab] = valid_sub_tabs

        return valid_tab_tree

    return tab_tree


def get_current_tab_name(context):
    match = context['request'].resolver_match
    namespace_size = len(match.namespaces)
    if namespace_size > 2:
        # Sub tabs - update mode (e.g: parcours_doctoral:update:curriculum:experience_detail)
        return match.namespaces[2]
    if namespace_size == 2 and match.namespaces[1] != 'update':
        # Sub tabs - read mode (e.g: parcours_doctoral:curriculum:experience_detail)
        return match.namespaces[1]
    # Main tabs (e.g: parcours_doctoral:curriculum or parcours_doctoral:update:curriculum)
    return match.url_name


@register.inclusion_tag('parcours_doctoral/tags/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, doctorate=None, with_submit=False):
    """Display current tabs given context (if with_submit=True, display the submit button within tabs)"""
    current_tab_name = get_current_tab_name(context)

    # Create a new tab tree based on the default one but depending on the permissions links
    tab_tree = TAB_TREES['doctorate']
    context['tab_tree'] = get_valid_tab_tree(tab_tree, doctorate)

    return {
        'active_parent': _get_active_parent(tab_tree, current_tab_name),
        'doctorate': doctorate,
        'doctorate_uuid': context['view'].kwargs.get('pk', ''),
        'with_submit': with_submit,
        **context.flatten(),
    }


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = TAB_TREES['doctorate']
    return current_tab_tree.get(_get_active_parent(current_tab_tree, current_tab_name), [])


@register.simple_tag(takes_context=True)
def get_current_parent_tab(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = TAB_TREES['doctorate']
    return _get_active_parent(current_tab_tree, current_tab_name)


@register.simple_tag(takes_context=True)
def get_current_tab(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = TAB_TREES['doctorate']
    return next(
        (tab for subtabs in current_tab_tree.values() for tab in subtabs if tab.name == current_tab_name),
        None,
    )


@register.inclusion_tag('parcours_doctoral/tags/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context, doctorate=None, tabs=None):
    """Display current subtabs given context (if tabs is specified, display provided tabs)"""
    current_tab_name = get_current_tab_name(context)
    return {
        'subtabs': tabs or current_subtabs(context),
        'doctorate': doctorate,
        'doctorate_uuid': context['view'].kwargs.get('pk', ''),
        'active_tab': current_tab_name,
        **context.flatten(),
    }


@register.inclusion_tag('parcours_doctoral/tags/field_data.html')
def field_data(
    name,
    data=None,
    css_class=None,
    hide_empty=False,
    translate_data=False,
    inline=False,
    html_tag='',
    empty_value=_('Incomplete field'),
    tooltip=None,
):
    if isinstance(data, list):
        template_string = "{% load osis_document %}{% if files %}{% document_visualizer files %}{% endif %}"
        template_context = {'files': data}
        data = template.Template(template_string).render(template.Context(template_context))

    elif isinstance(data, bool):
        data = _('Yes') if data else _('No')
    elif translate_data is True:
        data = _(data)

    if inline is True:
        name = _("%(label)s:") % {'label': name}
        css_class = (css_class + ' inline-field-data') if css_class else 'inline-field-data'
    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
        'html_tag': html_tag,
        'empty_value': empty_value,
        'tooltip': tooltip,
    }


@register_panel('parcours_doctoral/tags/panel.html', takes_context=True)
def panel(context, title='', title_level=4, additional_class='', **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :param title_level: the title level
    :param additional_class: css class to add
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['title_level'] = title_level
    context['additional_class'] = additional_class
    context['attributes'] = {k.replace('_', '-'): v for k, v in kwargs.items()}
    return context


@register.simple_tag(takes_context=True)
def get_dashboard_links(context):
    from parcours_doctoral.services.doctorate import DoctorateService

    with suppress(UnauthorizedException, NotFoundException, ForbiddenException):
        return DoctorateService.get_dashboard_links(context['request'].user.person)
    return {}


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def split(string: str, delimiter=','):
    return string.split(delimiter)


@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


@register.filter
def can_read_tab(doctorate, tab):
    """Return true if the specified tab can be opened in reading mode for this doctorate, otherwise return False"""
    return _can_access_tab(doctorate, str(tab), READ_ACTIONS_BY_TAB)


@register.filter
def can_update_tab(doctorate, tab):
    """Return true if the specified tab can be opened in writing mode for this doctorate, otherwise return False"""
    return _can_access_tab(doctorate, str(tab), UPDATE_ACTIONS_BY_TAB)


@register.filter
def add_str(arg1, arg2):
    """Return the concatenation of two arguments."""
    return f'{arg1}{arg2}'


@register.inclusion_tag('parcours_doctoral/tags/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False, html_tooltip=False):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
        'html_tooltip': html_tooltip,
    }


@register.filter
def status_as_class(activity):
    status = activity
    if hasattr(activity, 'status'):
        status = activity.status
    elif isinstance(activity, dict):
        status = activity['status']
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(str(status), 'info')


@register.simple_tag
def display(*args):
    """Display args if their value is not empty, can be wrapped by parenthesis, or separated by comma or dash"""
    ret = []
    iterargs = iter(args)
    nextarg = next(iterargs)
    while nextarg != StopIteration:
        if nextarg == "(":
            reduce_wrapping = [next(iterargs, None)]
            while reduce_wrapping[-1] != ")":
                reduce_wrapping.append(next(iterargs, None))
            ret.append(reduce_wrapping_parenthesis(*reduce_wrapping[:-1]))
        elif nextarg == ",":
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None)))
        elif nextarg in ["-", ':']:
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None), separator=f" {nextarg} "))
        elif isinstance(nextarg, str) and len(nextarg) > 1 and re.match(r'\s', nextarg[0]):
            ret, suffixed_val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(f"{suffixed_val}{nextarg}" if suffixed_val else "")
        else:
            ret.append(SafeString(nextarg) if nextarg else '')
        nextarg = next(iterargs, StopIteration)
    return SafeString("".join(ret))


@register.simple_tag
def reduce_wrapping_parenthesis(*args):
    """Display args given their value, wrapped by parenthesis"""
    ret = display(*args)
    if ret:
        return SafeString(f"({ret})")
    return ret


@register.simple_tag
def reduce_list_separated(arg1, arg2, separator=", "):
    """Display args given their value, joined by separator"""
    if arg1 and arg2:
        return separator.join([SafeString(arg1), SafeString(arg2)])
    elif arg1:
        return SafeString(arg1)
    elif arg2:
        return SafeString(arg2)
    return ""


def report_ects(activity, categories, added, validated, parent_category=None):
    if not hasattr(activity, 'ects'):
        return added, validated
    status = str(activity.status)
    if status != StatutActivite.REFUSEE.name:
        added += activity.ects
    if status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
        return added, validated
    category = str(activity.category)
    index = int(status == StatutActivite.ACCEPTEE.name)
    if status == StatutActivite.ACCEPTEE.name:
        validated += activity.ects
    elif category == CategorieActivite.CONFERENCE.name or category == CategorieActivite.SEMINAR.name:
        categories[_("Participation")][index] += activity.ects
    elif category == CategorieActivite.COMMUNICATION.name and (
        activity.get('parent') is None or parent_category == CategorieActivite.CONFERENCE.name
    ):
        categories[_("Scientific communication")][index] += activity.ects
    elif category == CategorieActivite.PUBLICATION.name and (
        activity.get('parent') is None or parent_category == CategorieActivite.CONFERENCE.name
    ):
        categories[_("Publication")][index] += activity.ects
    elif category == CategorieActivite.COURSE.name:
        categories[_("Course units and courses")][index] += activity.ects
    elif category == CategorieActivite.SERVICE.name:
        categories[_("Services")][index] += activity.ects
    elif (
        category == CategorieActivite.RESIDENCY.name
        or activity.get('parent')
        and parent_category == CategorieActivite.RESIDENCY.name
    ):
        categories[_("Scientific residencies")][index] += activity.ects
    elif category == CategorieActivite.VAE.name:
        categories[_("VAE")][index] += activity.ects
    return added, validated


@register.inclusion_tag('parcours_doctoral/includes/training_categories.html')
def training_categories(activities):
    added, validated = 0, 0

    categories = {
        _("Participation"): [0, 0],
        _("Scientific communication"): [0, 0],
        _("Publication"): [0, 0],
        _("Course units and courses"): [0, 0],
        _("Services"): [0, 0],
        _("VAE"): [0, 0],
        _("Scientific residencies"): [0, 0],
        _("Confirmation exam"): [0, 0],
        _("Thesis defense"): [0, 0],
    }
    for activity in activities:
        if not hasattr(activity, 'ects'):
            continue
        # Increment global counts
        status = str(activity.status)
        if status != StatutActivite.REFUSEE.name:
            added += activity.ects
        if status == StatutActivite.ACCEPTEE.name:
            validated += activity.ects
        if status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
            continue

        # Increment category counts
        index = int(status == StatutActivite.ACCEPTEE.name)
        category = str(activity.category)
        if category == CategorieActivite.CONFERENCE.name or category == CategorieActivite.SEMINAR.name:
            categories[_("Participation")][index] += activity.ects
        elif activity.object_type == "Communication" or activity.object_type == "ConferenceCommunication":
            categories[_("Scientific communication")][index] += activity.ects
        elif activity.object_type == "Publication" or activity.object_type == "ConferencePublication":
            categories[_("Publication")][index] += activity.ects
        elif category == CategorieActivite.SERVICE.name:
            categories[_("Services")][index] += activity.ects
        elif "Residency" in activity.object_type:
            categories[_("Scientific residencies")][index] += activity.ects
        elif category == CategorieActivite.VAE.name:
            categories[_("VAE")][index] += activity.ects
        elif category in [CategorieActivite.COURSE.name, CategorieActivite.UCL_COURSE.name]:
            categories[_("Course units and courses")][index] += activity.ects
        elif category == CategorieActivite.PAPER.name and activity.type == ChoixTypeEpreuve.CONFIRMATION_PAPER.name:
            categories[_("Confirmation exam")][index] += activity.ects
        elif category == CategorieActivite.PAPER.name:
            categories[_("Thesis defense")][index] += activity.ects
    if not added:
        return {}
    return {
        'display_table': any(cat_added + cat_validated for cat_added, cat_validated in categories.values()),
        'categories': categories,
        'added': added,
        'validated': validated,
    }


@register.filter
def status_list(activity):
    statuses = {str(activity['status'])}
    for child in activity['children']:
        statuses.add(str(child['status']))
    return ','.join(statuses)


@register.filter
def get_academic_year(year: Union[int, str]):
    """Return the academic year related to a specific year."""
    return format_academic_year(year)


@register.filter
def snake_case(value):
    return to_snake_case(str(value))


@register.simple_tag(takes_context=True)
def get_country_name(context, iso_code: str):
    """Return the country name."""
    if not iso_code:
        return ''
    translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'
    result = CountriesService.get_country(iso_code=iso_code, person=context['request'].user.person)
    return getattr(result, translated_field, '')


@register.filter(is_safe=False)
def default_if_none_or_empty(value, arg):
    """If value is None or empty, use given default."""
    return value if value not in EMPTY_VALUES else arg


@register.simple_tag
def interpolate(string, **kwargs):
    """Interpolate variables inside a string"""
    return string % kwargs


@register.simple_tag(takes_context=True)
def edit_external_member_form(context, membre: 'SupervisionDTOPromoteur'):
    """Get an edit form"""
    initial = membre.to_dict()
    initial['pays'] = initial['code_pays']
    return DoctorateMemberSupervisionForm(
        prefix=f"member-{membre.uuid}",
        person=context['user'].person,
        initial=initial,
    )


@register.filter
def diplomatic_post_name(diplomatic_post):
    """Get the name of a diplomatic post"""
    if diplomatic_post:
        return getattr(diplomatic_post, 'nom_francais' if get_language() == settings.LANGUAGE_CODE else 'nom_anglais')


@register.simple_tag
def form_fields_are_empty(form, *fields):
    """Return True if the form fields are empty."""
    return all(form[field_name].value() in form[field_name].field.empty_values for field_name in fields)


@register.simple_tag
def value_if_all(value, *conditions):
    """Return the value if all conditions are true."""
    return value if all(conditions) else ''


@register.simple_tag
def value_if_any(value, *conditions):
    """Return the value if any condition is true."""
    return value if any(conditions) else ''