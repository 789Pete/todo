import json

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from apps.tasks.models import Tag, Task


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.RadioSelect(),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        name = name.strip()
        if not name:
            raise ValidationError("Tag name cannot be empty.")
        return name


class TaskForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "status", "priority", "due_date", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }
        error_messages = {
            "title": {
                "required": "Please enter a task title.",
                "max_length": "Title is too long (maximum 200 characters).",
            },
            "due_date": {
                "invalid": "Please enter a valid date.",
            },
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["tags"].queryset = Tag.objects.filter(user=user)
        # Store tag colors for template rendering (JSON-safe)
        self.tag_colors = mark_safe(
            json.dumps({str(tag.pk): tag.color for tag in self.fields["tags"].queryset})
        )

    def clean_title(self):
        title = self.cleaned_data["title"]
        title = title.strip()
        if not title:
            raise ValidationError("Title cannot be empty.")
        return title

    def clean_tags(self):
        tags = self.cleaned_data.get("tags", [])
        if len(tags) > 5:
            raise ValidationError("A task cannot have more than 5 tags.")
        return tags
