# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy
from osis_parcours_doctoral_sdk.model.parcours_doctoral_dto import ParcoursDoctoralDTO

from parcours_doctoral.contrib.enums.training import (
    ChoixComiteSelection,
    ChoixStatutPublication,
    ChoixTypeEpreuve,
    ContexteFormation,
)
from parcours_doctoral.contrib.forms import (
    BooleanRadioSelect,
    CustomDateInput,
    SelectOrOtherField,
    get_academic_years_choices,
    get_country_initial_choices,
    DoctorateFileUploadField as FileUploadField,
    autocomplete,
)

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
    participating_proof = FileUploadField(label=_("Participation certification"), max_files=1)
    start_date = forms.DateField(label=_("Start date"), widget=CustomDateInput())
    end_date = forms.DateField(label=_("End date"), widget=CustomDateInput())
    participating_days = forms.DecimalField(
        label=_("Number of days participating"),
        max_digits=3,
        decimal_places=1,
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
    role = forms.CharField(label=_("Role"), max_length=100)
    keywords = forms.CharField(label=_("Keywords"), max_length=100)
    journal = forms.CharField(label=_("Journal or publishing house name"), max_length=100)
    publication_status = forms.ChoiceField(choices=ChoixStatutPublication.choices())
    hour_volume = forms.CharField(max_length=100, label=_("Total hourly volume"))
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
        help_texts = {
            'title': _("Name in the language of the manifestation"),
        }


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

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
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
            'title': _("Publication title"),
            'start_date': _("Publication date"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'acceptation_proof': _("Proof of acceptance or publication"),
            'publication_status': _("Publication status"),
        }


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
        label=_("Title of the communication"),
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
            'title': _("Activity name"),
            'start_date': _("Activity date"),
            'website': _("Event website"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
            'committee': _("Selection committee"),
            'summary': _("Summary of the communication"),
        }


class PublicationForm(ActivityFormMixin, forms.Form):
    object_type = "Publication"
    template_name = "parcours_doctoral/forms/training/publication.html"
    type = ConfigurableActivityTypeField('publication_types', label=_("Publication type"))

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'authors',
            'role',
            'keywords',
            'summary',
            'journal',
            'publication_status',
            'dial_reference',
            'ects',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'title': _("Publication title"),
            'start_date': _("Publication date"),
            'publication_status': _("Publication status"),
            'acceptation_proof': _("Proof of publication"),
        }


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
            'participating_proof',
            'comment',
        ]
        labels = {
            'subtitle': _("Activity description"),
            'participating_proof': _("Proof (if applicable)"),
        }


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
            'start_date': _("Activity date"),
            'website': _("Event website"),
            'summary': _("Summary of the communication"),
            'participating_proof': _("Attestation of the communication"),
        }


class ServiceForm(ActivityFormMixin, forms.Form):
    object_type = "Service"
    template_name = "parcours_doctoral/forms/training/service.html"
    type = ConfigurableActivityTypeField("service_types", label=_("Activity type"))

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
            'title': _("Activity name"),
            'participating_proof': _("Proof (if applicable)"),
            'organizing_institution': _("Institution"),
        }


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
            'hour_volume',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Activity name"),
            'participating_proof': _("Proof of participation for the whole activity"),
        }


class SeminarCommunicationForm(ActivityFormMixin, forms.Form):
    object_type = "SeminarCommunication"
    template_name = "parcours_doctoral/forms/training/seminar_communication.html"
    is_online = IsOnlineField()

    class Meta:
        fields = [
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'authors',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'start_date': _("Presentation date"),
            'authors': _("Speaker"),
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
            'ects',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Activity name"),
            'authors': _("Course unit instructor (if applicable)"),
            'participating_proof': _("Proof of participation or success"),
        }


class ComplementaryCourseForm(CourseForm):
    """Course form for complementary training"""

    object_type = "Course"
    type = ConfigurableActivityTypeField("complementary_course_types", label=_("Activity type"))


class PaperForm(ActivityFormMixin, forms.Form):
    object_type = "Paper"
    template_name = "parcours_doctoral/forms/training/paper.html"
    type = forms.ChoiceField(label=_("Type of paper"), choices=ChoixTypeEpreuve.choices())

    class Meta:
        fields = [
            'type',
            'ects',
            'comment',
        ]


class UclCourseForm(ActivityFormMixin, forms.Form):
    object_type = "UclCourse"
    template_name = "parcours_doctoral/forms/training/ucl_course.html"
    academic_year = forms.TypedChoiceField(
        coerce=int,
        empty_value=None,
        label=_("Academic year"),
        widget=autocomplete.ListSelect2(),
    )
    learning_unit_year = forms.CharField(
        label=_("Learning unit"),
        widget=autocomplete.ListSelect2(
            url='parcours_doctoral:autocomplete:learning-unit-years',
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for an EU code (outside the EU of the form)'),
            },
            forward=["academic_year"],
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].choices = [
            choice
            for choice in get_academic_years_choices(self.person)
            if not choice[0] or choice[0] >= datetime.date.today().year
        ]
        self.fields['learning_unit_year'].required = True

        # Filter out disabled contexts
        choices = dict(self.fields['context'].widget.choices)
        # TODO be sure that the following lines are not needed
        # if self.doctorate.type_admission == AdmissionType.PRE_ADMISSION.name:
        #     del choices[ContexteFormation.DOCTORAL_TRAINING.name]
        if not self.config_types.get('is_complementary_training_enabled'):
            del choices[ContexteFormation.COMPLEMENTARY_TRAINING.name]
        self.fields['context'].widget.choices = list(choices.items())

        # Initialize values
        if self.initial.get('learning_unit_year'):
            acronym = self.initial['learning_unit_year']
            self.fields['learning_unit_year'].widget.choices = [
                (acronym, f"{acronym} - {self.initial['learning_unit_title']}")
            ]

    class Meta:
        fields = [
            'context',
            'academic_year',
            'learning_unit_year',
        ]


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
