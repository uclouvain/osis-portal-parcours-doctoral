# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial
from typing import List, Mapping, Optional, Union

from django import forms
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileUploadField

from parcours_doctoral.services.organisation import EntitiesService
from parcours_doctoral.services.reference import (
    AcademicYearService,
    CountriesService,
    LanguageService,
    SuperiorInstituteService,
)
from parcours_doctoral.utils import (
    format_entity_title,
    format_scholarship,
    format_school_title,
)
from reference.services.scholarship import ScholarshipService

EMPTY_CHOICE = (('', ' - '),)
EMPTY_VALUE = '__all__'
FORM_SET_PREFIX = '__prefix__'
FOLLOWING_FORM_SET_PREFIX = '__prefix_1__'
OSIS_DOCUMENT_UPLOADER_CLASS = 'document-uploader'
OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX = '__{}__'.format(OSIS_DOCUMENT_UPLOADER_CLASS)
PDF_MIME_TYPE = 'application/pdf'
JPEG_MIME_TYPE = 'image/jpeg'
PNG_MIME_TYPE = 'image/png'
IMAGE_MIME_TYPES = [JPEG_MIME_TYPE, PNG_MIME_TYPE]
DEFAULT_MIME_TYPES = [PDF_MIME_TYPE] + IMAGE_MIME_TYPES
MAX_FILE_UPLOAD_SIZE = 1024 * 1024 * 10


def get_country_initial_choices(iso_code=None, person=None, loaded_country=None):
    """Return the unique initial choice for a country when data is either set from initial or from webservice."""
    if not iso_code and not loaded_country:
        return EMPTY_CHOICE
    country = loaded_country if loaded_country else CountriesService.get_country(iso_code=iso_code, person=person)
    if not country:
        return EMPTY_CHOICE
    return EMPTY_CHOICE + (
        (country.iso_code, country.name if get_language() == settings.LANGUAGE_CODE else country.name_en),
    )


def get_language_initial_choices(code, person):
    """Return the unique initial choice for a language when data is either set from initial or from webservice."""
    if not code:
        return EMPTY_CHOICE
    language = LanguageService.get_language(code=code, person=person)
    return EMPTY_CHOICE + (
        (language.code, language.name if get_language() == settings.LANGUAGE_CODE else language.name_en),
    )


def get_thesis_institute_initial_choices(uuid, person):
    """Return the unique initial choice for an institute when data is either set from initial or webservice."""
    if not uuid:
        return EMPTY_CHOICE
    institute = EntitiesService.get_ucl_entity(person=person, uuid=uuid)
    return EMPTY_CHOICE + ((institute.uuid, format_entity_title(entity=institute)),)


def get_superior_institute_initial_choices(institute_id, person):
    """Return the superior non university choices when data is either set from initial or webservice."""
    if not institute_id:
        return EMPTY_CHOICE

    institute = SuperiorInstituteService.get_superior_institute(
        person=person,
        uuid=institute_id,
    )

    return EMPTY_CHOICE + ((institute.uuid, format_school_title(school=institute)),)


def get_thesis_location_initial_choices(value):
    """Return the unique initial choice for a thesis location when data is either set from initial or webservice."""
    return EMPTY_CHOICE if not value else EMPTY_CHOICE + ((value, value),)


def get_scholarship_choices(uuid, person):
    """Return the unique initial choice for the campus."""
    if not uuid:
        return EMPTY_CHOICE
    scholarship = ScholarshipService.get_scholarship(
        person=person,
        scholarship_uuid=uuid,
    )
    return EMPTY_CHOICE + ((uuid, format_scholarship(scholarship)),)


class CustomDateInput(forms.DateInput):
    def __init__(self, attrs=None, format='%d/%m/%Y'):
        if attrs is None:
            attrs = {
                'placeholder': _("dd/mm/yyyy"),
                'data-mask' '': '00/00/0000',
                'autocomplete': 'off',
            }
        super().__init__(attrs, format)

    class Media:
        js = ('jquery.mask.min.js',)


RadioBooleanField = partial(
    forms.TypedChoiceField,
    coerce=lambda value: value == 'True',
    choices=((True, _('Yes')), (False, _('No'))),
    widget=forms.RadioSelect,
    empty_value=None,
)


class DoctorateFileUploadField(FileUploadField):
    def __init__(self, **kwargs):
        kwargs.setdefault('mimetypes', DEFAULT_MIME_TYPES)
        kwargs.setdefault('max_size', MAX_FILE_UPLOAD_SIZE)

        super().__init__(**kwargs)


class SelectOrOtherWidget(forms.MultiWidget):
    """Form widget to handle a configurable (from CDDConfiguration) list of choices, or other"""

    template_name = 'parcours_doctoral/widgets/select_or_other_widget.html'
    media = forms.Media(
        js=[
            'js/dependsOn.min.js',
            'parcours_doctoral/select_or_other.js',
        ]
    )

    def __init__(self, *args, **kwargs):
        widgets = {
            '': forms.Select(),
            'other': forms.TextInput(),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # No value, no value to both fields
        if not value:
            return [None, None]
        # Pass value to radios if part of choices
        if value in dict(self.widgets[0].choices):
            return [value, '']
        # else pass value to textinput
        return ['other', value]

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        subwidgets = context['widget']['subwidgets']
        # Remove the title attribute on first widget and handle tooltip
        subwidgets[0]['attrs'].pop('help_text', None)
        subwidgets[1]['help_text'] = subwidgets[1]['attrs'].pop('help_text', None)
        # Remove the required attribute on textinput
        subwidgets[1]['attrs']['required'] = False
        return context


class SelectOrOtherField(forms.MultiValueField):
    """Form field to handle a list of choices, or other"""

    widget = SelectOrOtherWidget
    select_class = forms.ChoiceField

    def __init__(self, choices: Optional[Union[List[str], Mapping[str, str]]] = None, *args, **kwargs):
        select_kwargs = {}
        if choices is not None:
            choices = zip(choices, choices) if not isinstance(choices[0], (list, tuple)) else choices
            select_kwargs['choices'] = self.choices = list(choices) + [('other', _("Other"))]
        fields = [self.select_class(required=False, **select_kwargs), forms.CharField(required=False)]
        super().__init__(fields, require_all_fields=False, *args, **kwargs)

    def get_bound_field(self, form, field_name):
        if not self.widget.widgets[0].choices:
            self.widget.widgets[0].choices = self.choices
        return super().get_bound_field(form, field_name)

    def validate(self, value):
        # We do require all fields, but we want to check the final (compressed value)
        super(forms.MultiValueField, self).validate(value)

    def compress(self, data_list):
        # On save, take the other value if "other" is chosen
        if len(data_list) == 2:
            radio, other = data_list
            return radio if radio != "other" else other
        return ''

    def clean(self, value):
        # Dispatch the correct values to each field before regular cleaning
        radio, other = value
        if hasattr(self, 'choices') and radio not in self.choices and other is None:
            value = ['other', radio]
        return super().clean(value)

    def widget_attrs(self, widget):
        if self.help_text:
            return {'help_text': self.help_text}
        return super().widget_attrs(widget)


class BooleanRadioSelect(forms.RadioSelect):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Override to explicitly set initial selected option to 'False' value
        if value is None:
            context['widget']['optgroups'][0][1][0]['selected'] = True
            context['widget']['optgroups'][0][1][0]['attrs']['checked'] = True
        return context
