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
from functools import partial

from django import forms
from django.core import validators
from django.utils.dates import MONTHS_ALT
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto import ParcoursDoctoralDTO
from osis_parcours_doctoral_sdk.model.type_enum import (
    TypeEnum as PaperTypeEnum,
)

from base.models.person import Person
from parcours_doctoral.contrib.enums.training import (
    ChoixComiteSelection,
    ChoixRolePublication,
    ChoixStatutPublication,
    ChoixTypeEpreuve,
    ChoixTypeVolume,
    ContexteFormation,
)
from parcours_doctoral.contrib.forms import (
    EMPTY_CHOICE,
    BooleanRadioSelect,
    CustomDateInput,
    SelectOrOtherField,
    autocomplete,
    get_country_initial_choices,
)
from parcours_doctoral.contrib.forms import DoctorateFileUploadField as FileUploadField
from reference.services.academic_year import AcademicYearService

__all__ = [
    "BatchActivityForm",
    "CommunicationForm",
    "ConferenceCommunicationForm",
    "ConferenceForm",
    "ConferencePublicationForm",
    "CourseForm",
    "PaperForm",
    "PublicationForm",
    "ResidencyCommunicationForm",
    "ResidencyForm",
    "SeminarCommunicationForm",
    "SeminarForm",
    "ServiceForm",
    "ValorisationForm",
    "ComplementaryCourseForm",
    "UclCourseForm",
    "AssentForm",
]


INSTITUTION_UCL = "UCLouvain"
MINIMUM_YEAR = 2000


def year_choices():
    return [EMPTY_CHOICE[0]] + [(int(year), year) for year in range(datetime.date.today().year, MINIMUM_YEAR, -1)]


def month_choices():
    return [EMPTY_CHOICE[0]] + [(int(index), month) for index, month in MONTHS_ALT.items()]


class ConfigurableActivityTypeField(SelectOrOtherField):
    select_class = forms.CharField

    def __init__(self, source: str = '', *args, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        # Update radio choices from CDD configuration
        values = form.config_types.get(self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)


IsOnlineField = partial(
    forms.BooleanField,
    label=_("Online or in person"),
    initial=False,
    required=False,
    widget=forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
)


class ActivityFormMixin(forms.Form):
    config_types = {}

    type = ConfigurableActivityTypeField(label=_("Activity type"))
    title = forms.CharField(label=pgettext_lazy("doctorate", "Title"), max_length=200)
    participating_proof = FileUploadField(label=_("Participation certification"), max_files=2)
    start_date = forms.DateField(label=_("Start date"), widget=CustomDateInput())
    end_date = forms.DateField(label=_("End date"), widget=CustomDateInput())
    participating_days = forms.DecimalField(
        label=_("Number of days participating"),
        max_digits=3,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
    )
    is_online = IsOnlineField()
    country = forms.CharField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:country",
            attrs={
                "data-html": True,
            },
        ),
    )
    city = forms.CharField(label=_("City"), max_length=100)
    organizing_institution = forms.CharField(label=_("Organising institution"), max_length=100)
    website = forms.URLField(label=_("Website"))
    committee = forms.ChoiceField(
        choices=ChoixComiteSelection.choices(),
    )
    dial_reference = forms.CharField(label=_("Reference DIAL.Pr"), max_length=100)
    acceptation_proof = FileUploadField(label=_("Participation certification"), max_files=1)
    summary = FileUploadField(label=pgettext_lazy("paper summary", "Summary"), max_files=1)
    subtype = forms.CharField(label=_("Activity subtype"), max_length=100)
    subtitle = forms.CharField(widget=forms.Textarea())
    authors = forms.CharField(label=_("Authors"), max_length=100)
    role = forms.ChoiceField(label=_("Role"), choices=ChoixRolePublication.choices())
    keywords = forms.CharField(label=_("Keywords"), max_length=100)
    journal = forms.CharField(label=_("Journal, publishing house or depository institution"), max_length=100)
    publication_status = forms.ChoiceField(choices=ChoixStatutPublication.choices())
    is_publication_national = forms.BooleanField(
        label=_("Is publication national"),
        initial=True,
        required=False,
        widget=forms.RadioSelect(choices=((False, _("International publication")), (True, _("National publication")))),
    )
    with_reading_committee = forms.BooleanField(
        label=_("With reading committee"),
        initial=False,
        required=False,
        widget=forms.RadioSelect(
            choices=((False, _("Without reading committee")), (True, _("With reading committee")))
        ),
    )
    mark = forms.CharField(
        max_length=100,
        label=_("Mark or honours obtained"),
    )
    hour_volume = forms.CharField(
        max_length=100,
        label=_("Total hourly volume"),
        widget=forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
    )
    hour_volume_type = forms.ChoiceField(choices=ChoixTypeVolume.choices())
    ects = forms.DecimalField(
        label=_("ECTS credits"),
        help_text=_(
            'Consult the credits grid released by your domain doctoral commission.'
            ' Refer to the website of your commission for more details.'
        ),
        max_digits=4,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        validators=[validators.MinValueValidator(0)],
    )
    comment = forms.CharField(label=_("Comment"), widget=forms.Textarea())
    context = forms.ChoiceField(label=_("Context"), choices=ContexteFormation.choices())

    def __init__(
        self,
        doctorate: ParcoursDoctoralDTO = None,
        config_types=None,
        person=None,
        *args,
        **kwargs,
    ) -> None:
        self.doctorate = doctorate
        self.person = person
        self.config_types = config_types or {}
        super().__init__(*args, **kwargs)
        # Remove unneeded fields
        for field_name in list(self.fields.keys()):
            if field_name not in self.Meta.fields:
                del self.fields[field_name]
        # Make all fields not required and apply label overrides
        labels = getattr(self.Meta, 'labels', {})
        for field_name in self.fields:
            if field_name != 'type' and not (
                isinstance(self.fields[field_name], SelectOrOtherField) and field_name == 'organizing_institution'
            ):
                self.fields[field_name].required = False
            self.fields[field_name].label = labels.get(field_name, self.fields[field_name].label)
        if 'country' in self.fields:
            self.fields['country'].widget.choices = get_country_initial_choices(
                self.data.get(self.add_prefix("country"), self.initial.get("country")),
                person,
            )

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date > datetime.date.today():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        if end_date and end_date > datetime.date.today():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return end_date

    def clean(self):
        data = super().clean()
        if data.get('start_date') and data.get('end_date') and data.get('start_date') > data.get('end_date'):
            self.add_error('start_date', _("The start date must be earlier than or the same as the end date."))
        return data

    class Media:
        js = ('js/dependsOn.min.js',)


class ConferenceForm(ActivityFormMixin, forms.Form):
    object_type = "Conference"
    template_name = "parcours_doctoral/forms/training/conference.html"
    type = ConfigurableActivityTypeField('conference_types', label=_("Activity type"))
    is_online = IsOnlineField()

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'end_date',
            'participating_days',
            'hour_volume',
            'is_online',
            'website',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'website': _("Event website"),
            'ects': _("ECTS for the participation"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = _("Please specify the title in the language of the manifestation")
        self.fields['participating_days'].help_text = _(
            "Please specify either a hourly volume or a number of participating days"
        )
        self.fields['hour_volume'].help_text = _(
            "Please specify either a hourly volume or a number of participating days"
        )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('participating_days') and not cleaned_data.get('hour_volume'):
            self.add_error(
                'participating_days',
                forms.ValidationError(_("Please specify either a hourly volume or a number of participating days")),
            )
            self.add_error(
                'hour_volume',
                forms.ValidationError(_("Please specify either a hourly volume or a number of participating days")),
            )
        return cleaned_data


class ConferenceCommunicationForm(ActivityFormMixin, forms.Form):
    object_type = "ConferenceCommunication"
    template_name = "parcours_doctoral/forms/training/conference_communication.html"
    type = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral presentation"),
            _("Poster"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = _("Specify the title in the language of the activity")
        self.fields['participating_proof'].help_text = _(
            "A document proving that the communication was done (i.e. communication certificate)"
        )

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'summary',
            'committee',
            'acceptation_proof',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'summary': _("Summary of the communication"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Attestation of the communication"),
            'committee': _("Selection committee"),
        }


class ConferencePublicationForm(ActivityFormMixin, forms.Form):
    object_type = "ConferencePublication"
    template_name = "parcours_doctoral/forms/training/conference_publication.html"
    type = ConfigurableActivityTypeField('conference_publication_types', label=_("Publication type"))

    start_date_month = forms.TypedChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
        required=True,
        coerce=int,
    )
    start_date_year = forms.TypedChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
        required=True,
        coerce=int,
        help_text=_(
            "For a released text, specify the month and year of publication."
            " Else, specify the month and year of the manuscript."
        ),
    )

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'start_date_month',
            'start_date_year',
            'start_date',
            'publication_status',
            'authors',
            'role',
            'keywords',
            'summary',
            'committee',
            'journal',
            'dial_reference',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'type': _("Publication type"),
            'title': _("Publication title (in the publication language)"),
            'start_date': _("Date"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'acceptation_proof': _("Proof of acceptance or publication"),
            'publication_status': _("Publication status"),
        }

    def __init__(self, *args, **kwargs):
        if kwargs['initial'].get('start_date'):
            kwargs['initial'].update(
                {
                    'start_date_month': kwargs['initial']['start_date'].month,
                    'start_date_year': kwargs['initial']['start_date'].year,
                }
            )

        super().__init__(*args, **kwargs)

        self.fields['authors'].help_text = _(
            'Please use the following format for inputting the first and last name: "Monteiro, M. et Marti, A. C."'
        )
        self.fields['publication_status'].help_text = _("Refer to the website of your commission for more details.")
        self.fields['acceptation_proof'].help_text = _(
            "Submit a proof, for example a letter from the editor,"
            " a delivery attestation, the first page of the publication, ..."
        )

    def clean(self):
        data = super().clean()
        if data.get('start_date_year') and data.get('start_date_month'):
            data['start_date'] = datetime.date(data['start_date_year'], data['start_date_month'], 1)
        return data


class CommunicationForm(ActivityFormMixin, forms.Form):
    object_type = "Communication"
    template_name = "parcours_doctoral/forms/training/communication.html"
    type = ConfigurableActivityTypeField('communication_types', label=_("Activity type"))
    subtype = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral presentation"),
            _("Poster"),
        ],
    )
    subtitle = forms.CharField(
        label=_("Communication title (in the activity language)"),
        max_length=200,
        required=False,
    )
    is_online = IsOnlineField()

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'subtitle',
            'summary',
            'committee',
            'acceptation_proof',
            'participating_proof',
            'dial_reference',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'start_date': _("Activity date"),
            'website': _("Event website"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
            'committee': _("Selection committee"),
            'summary': _("Summary of the communication"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].help_text = _("Specify the name of the event in which the communicate took place")
        self.fields['summary'].help_text = _(
            "Required field for some of the doctoral commissions."
            " Refer to the website of your commission for more detail."
        )


class PublicationForm(ActivityFormMixin, forms.Form):
    object_type = "Publication"
    template_name = "parcours_doctoral/forms/training/publication.html"
    type = ConfigurableActivityTypeField('publication_types', label=_("Publication type"))

    start_date_month = forms.TypedChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
        required=True,
        coerce=int,
    )
    start_date_year = forms.TypedChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
        required=True,
        coerce=int,
        help_text=_("If necessary, specify the date of publication, delivery, acceptation or of the manuscript"),
    )

    class Meta:
        fields = [
            'type',
            'is_publication_national',
            'title',
            'start_date_month',
            'start_date_year',
            'start_date',
            'authors',
            'role',
            'keywords',
            'summary',
            'journal',
            'publication_status',
            'with_reading_committee',
            'dial_reference',
            'ects',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'title': _("Title (in the publication language)"),
            'start_date': _("Date"),
            'publication_status': _("Status"),
            'acceptation_proof': _("Attestation"),
        }

    def __init__(self, *args, **kwargs):
        if kwargs['initial'].get('start_date'):
            kwargs['initial'].update(
                {
                    'start_date_month': kwargs['initial']['start_date'].month,
                    'start_date_year': kwargs['initial']['start_date'].year,
                }
            )

        super().__init__(*args, **kwargs)

        self.fields['authors'].help_text = _(
            'Please use the following format for inputting the first and last name: "Monteiro, M. et Marti, A. C."'
        )
        self.fields['publication_status'].help_text = _(
            "Specify the status of the publication or of the patent. Consult the website of your commission for "
            "more detail."
        )
        self.fields['acceptation_proof'].help_text = _(
            "Submit a proof, for example a letter from the editor,"
            " a delivery attestation, the first page of the publication, ..."
        )

    def clean(self):
        data = super().clean()
        if data.get('start_date_year') and data.get('start_date_month'):
            data['start_date'] = datetime.date(data['start_date_year'], data['start_date_month'], 1)
        return data


class ResidencyForm(ActivityFormMixin, forms.Form):
    object_type = "Residency"
    template_name = "parcours_doctoral/forms/training/residency.html"
    type = ConfigurableActivityTypeField('residency_types', label=_("Activity type"))

    class Meta:
        fields = [
            'type',
            'ects',
            'subtitle',
            'start_date',
            'end_date',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'organizing_institution': _("Institution"),
            'subtitle': _("Activity description"),
            'participating_proof': _("Attestation"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['type'].help_text = _("Refer to your commission website for more detail.")
        self.fields['participating_proof'].help_text = _(
            "Be careful, some doctorales commissions require an activity proof in their"
            " specifics dispositions. Refer to your commission specifics dispositions."
        )


class ResidencyCommunicationForm(ActivityFormMixin, forms.Form):
    object_type = "ResidencyCommunication"
    template_name = "parcours_doctoral/forms/training/residency_communication.html"
    type = SelectOrOtherField(choices=[_("Research seminar")], label=_("Activity type"))
    subtype = SelectOrOtherField(
        choices=[_("Oral presentation")],
        label=_("Type of communication"),
        required=False,
    )
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200, required=False)
    is_online = IsOnlineField()

    class Meta:
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'organizing_institution',
            'website',
            'subtitle',
            'ects',
            'summary',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'subtitle': _("Communication title (in the activity language)"),
            'start_date': _("Communication date"),
            'website': _("Event website"),
            'summary': _("Summary of the communication"),
            'participating_proof': _("Attestation of the communication"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].help_text = _("Specify the name of the event in which the communicate took place")
        self.fields['summary'].help_text = _(
            "Required field if some doctorals commissions, refer to your commission specifics dispositions."
        )


class ServiceForm(ActivityFormMixin, forms.Form):
    object_type = "Service"
    template_name = "parcours_doctoral/forms/training/service.html"
    type = ConfigurableActivityTypeField(
        "service_types",
        label=_("Service type"),
        help_text=_("Refer to your commission website for more detail."),
    )

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'organizing_institution',
            'hour_volume',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name or brief description"),
            'participating_proof': _("Attestation"),
            'organizing_institution': _("Institution"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['participating_proof'].help_text = _(
            "Be careful, some doctorales commissions require an activity proof in their"
            " specifics dispositions. Refer to your commission specifics dispositions."
        )


class SeminarForm(ActivityFormMixin, forms.Form):
    object_type = "Seminar"
    template_name = "parcours_doctoral/forms/training/seminar.html"
    type = ConfigurableActivityTypeField("seminar_types", label=_("Activity type"))

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'country',
            'city',
            'organizing_institution',
            'hour_volume',
            'hour_volume_type',
            'summary',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Activity name"),
            'participating_proof': _("Proof of participation for the whole activity"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hour_volume'].help_text = _(
            "Following the specifics of your domain doctoral commission,"
            " specify the total time dedicated to this activity"
        )
        self.fields['city'].help_text = _("If the seminar takes place in several places, leave this field empty.")


class SeminarCommunicationForm(ActivityFormMixin, forms.Form):
    object_type = "SeminarCommunication"
    template_name = "parcours_doctoral/forms/training/seminar_communication.html"
    is_online = IsOnlineField()

    class Meta:
        fields = [
            'title',
            'start_date',
            'is_online',
            'website',
            'authors',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the paper in the language of the activity"),
            'start_date': _("Presentation date"),
            'authors': _("First name and last name of the speaker"),
            'participating_proof': _("Certificate of participation in the presentation"),
        }


class ValorisationForm(ActivityFormMixin, forms.Form):
    object_type = "Valorisation"
    template_name = "parcours_doctoral/forms/training/valorisation.html"

    class Meta:
        fields = [
            'title',
            'subtitle',
            'summary',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': pgettext_lazy("doctorate", "Title"),
            'subtitle': _("Description"),
            'summary': _("Detailed curriculum vitae"),
            'participating_proof': _("Proof"),
        }


class CourseForm(ActivityFormMixin, forms.Form):
    object_type = "Course"
    template_name = "parcours_doctoral/forms/training/course.html"
    type = ConfigurableActivityTypeField("course_types", label=_("Activity type"))
    subtitle = forms.CharField(
        label=_("Course unit code (if applicable)"),
        help_text=_("As it appears in an official course catalogue"),
        max_length=200,
        required=False,
    )
    start_date = forms.DateField(
        label=_("Start date"),
        widget=CustomDateInput(),
        help_text=_(
            "For courses in the UCLouvain catalogue, the academic year "
            "begins on 14 September and ends on 13 September of the following year."
        ),
    )
    organizing_institution = SelectOrOtherField(choices=[INSTITUTION_UCL], label=_("Institution"), required=True)
    is_online = forms.BooleanField(
        label=_("Course unit with evaluation"),  # Yes, its another meaning, but we spare a db field
        initial=False,
        required=False,
        widget=BooleanRadioSelect(choices=((False, _("No")), (True, _("Yes")))),
    )

    class Meta:
        fields = [
            'type',
            'title',
            'subtitle',
            'organizing_institution',
            'start_date',
            'end_date',
            'academic_year',
            'hour_volume',
            'authors',
            'is_online',
            'mark',
            'ects',
            'participating_proof',
            'comment',
        ]
        labels = {
            'type': pgettext_lazy("parcours_doctoral course", "Course type"),
            'title': pgettext_lazy("parcours_doctoral course", "Title"),
            'authors': _("Organisers or academic responsibles"),
            'hour_volume': _("Hourly volume"),
            'participating_proof': _("Proof of participation or success"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['authors'].help_text = _("In the context of a course, specify the name of the professor")
        self.fields['title'].help_text = _("As it appears in an official course catalogue")


class ComplementaryCourseForm(CourseForm):
    """Course form for complementary training"""

    object_type = "Course"
    type = ConfigurableActivityTypeField("complementary_course_types", label=_("Activity type"))


class PaperForm(ActivityFormMixin, forms.Form):
    object_type = "Paper"
    template_name = "parcours_doctoral/forms/training/paper.html"
    type = forms.ChoiceField(label=_("Type of paper"))

    class Meta:
        fields = [
            'type',
            'ects',
            'comment',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only one paper by type can be created
        creatable_papers_types = self.config_types.creatable_papers_types

        if self.initial and self.initial.get('type'):
            creatable_papers_types.append(self.initial['type'])

        self.fields['type'].choices = (
            (enum.name, enum.value) for enum in ChoixTypeEpreuve if enum.name in creatable_papers_types
        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('type'):
            cleaned_data['type'] = PaperTypeEnum(cleaned_data['type'])

        return cleaned_data


class UclCourseForm(ActivityFormMixin, forms.Form):
    object_type = "UclCourse"
    template_name = "parcours_doctoral/forms/training/ucl_course.html"
    course = forms.CharField(
        label=_("Learning unit"),
        widget=autocomplete.ListSelect2(
            url='parcours_doctoral:autocomplete:learning-unit-years',
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for an EU code'),
            },
        ),
    )

    def __init__(self, *args, person: Person = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.academic_year = AcademicYearService.get_current_academic_year(person=person).year
        self.fields['course'].required = True

        # Filter out disabled contexts
        choices = dict(self.fields['context'].widget.choices)
        if not self.config_types.get('is_complementary_training_enabled'):
            del choices[ContexteFormation.COMPLEMENTARY_TRAINING.name]
        self.fields['context'].widget.choices = list(choices.items())

        selected_acronym = self.data.get(self.add_prefix('course'))
        if selected_acronym:
            self.fields['course'].widget.choices = [(selected_acronym, selected_acronym)]

        elif self.initial.get('course'):
            selected_acronym = self.initial['course']
            self.fields['course'].widget.choices = [
                (selected_acronym, f"{selected_acronym} - {self.initial['course_title']}")
            ]

    class Meta:
        fields = [
            'context',
            'course',
        ]

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['academic_year'] = self.academic_year
        return cleaned_data


class BatchActivityForm(forms.Form):
    activity_ids = forms.MultipleChoiceField(required=False)

    def __init__(self, uuids=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activity_ids'].choices = zip(uuids, uuids)

    def clean(self):
        data = super().clean()
        if not data.get('activity_ids'):
            raise forms.ValidationError(_("No activity selected."))
        return data


class AssentForm(forms.Form):
    approbation = forms.BooleanField(label=_("Approval"), required=False)
    commentaire = forms.CharField(label=_("Comment"), widget=forms.Textarea, required=False)

    class Media:
        js = ('js/dependsOn.min.js',)
