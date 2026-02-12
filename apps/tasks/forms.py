from django import forms
from django.core.exceptions import ValidationError

from apps.tasks.models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "priority", "due_date"]
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

    def clean_title(self):
        title = self.cleaned_data["title"]
        title = title.strip()
        if not title:
            raise ValidationError("Title cannot be empty.")
        return title
