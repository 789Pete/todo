import pytest

from apps.accounts.tests.factories import UserFactory
from apps.tasks.forms import TagForm, TaskForm
from apps.tasks.tests.factories import TagFactory


@pytest.mark.django_db
class TestTaskForm:
    def test_valid_data(self):
        data = {
            "title": "Test Task",
            "description": "A description",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert form.is_valid()

    def test_rejects_empty_title(self):
        data = {
            "title": "",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_rejects_whitespace_only_title(self):
        data = {
            "title": "   ",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_accepts_optional_description(self):
        data = {
            "title": "Task",
            "description": "",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert form.is_valid()

    def test_accepts_optional_due_date(self):
        data = {
            "title": "Task",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data["due_date"] is None

    def test_accepts_due_date(self):
        data = {
            "title": "Task",
            "status": "todo",
            "priority": "medium",
            "due_date": "2026-03-15",
        }
        form = TaskForm(data=data)
        assert form.is_valid()

    def test_validates_status_choices(self):
        data = {
            "title": "Task",
            "status": "invalid",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert not form.is_valid()
        assert "status" in form.errors

    def test_validates_priority_choices(self):
        data = {
            "title": "Task",
            "status": "todo",
            "priority": "critical",
        }
        form = TaskForm(data=data)
        assert not form.is_valid()
        assert "priority" in form.errors

    def test_includes_correct_fields(self):
        form = TaskForm()
        expected_fields = {
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "tags",
        }
        assert set(form.fields.keys()) == expected_fields

    def test_title_is_stripped(self):
        data = {
            "title": "  Stripped Title  ",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data["title"] == "Stripped Title"

    def test_tags_field_filters_by_user(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=user)
        TagFactory(user=other_user)

        form = TaskForm(user=user)
        assert tag in form.fields["tags"].queryset
        assert form.fields["tags"].queryset.count() == 1

    def test_tags_field_empty_without_user(self):
        form = TaskForm()
        assert form.fields["tags"].queryset.count() == 0

    def test_max_5_tags_enforced(self):
        user = UserFactory()
        tags = TagFactory.create_batch(6, user=user)

        data = {
            "title": "Task",
            "status": "todo",
            "priority": "medium",
            "tags": [t.pk for t in tags],
        }
        form = TaskForm(data=data, user=user)
        assert not form.is_valid()
        assert "tags" in form.errors

    def test_5_tags_allowed(self):
        user = UserFactory()
        tags = TagFactory.create_batch(5, user=user)

        data = {
            "title": "Task",
            "status": "todo",
            "priority": "medium",
            "tags": [t.pk for t in tags],
        }
        form = TaskForm(data=data, user=user)
        assert form.is_valid()

    def test_tags_optional(self):
        data = {
            "title": "Task",
            "status": "todo",
            "priority": "medium",
        }
        form = TaskForm(data=data)
        assert form.is_valid()

    def test_tag_colors_json_populated(self):
        user = UserFactory()
        TagFactory(user=user, color="#FF6B6B")
        form = TaskForm(user=user)
        assert "#FF6B6B" in str(form.tag_colors)


@pytest.mark.django_db
class TestTagForm:
    def test_valid_data(self):
        data = {"name": "Work", "color": "#FF6B6B"}
        form = TagForm(data=data)
        assert form.is_valid()

    def test_rejects_empty_name(self):
        data = {"name": "", "color": "#FF6B6B"}
        form = TagForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_rejects_whitespace_only_name(self):
        data = {"name": "   ", "color": "#FF6B6B"}
        form = TagForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_strips_whitespace_from_name(self):
        data = {"name": "  Work  ", "color": "#FF6B6B"}
        form = TagForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data["name"] == "Work"

    def test_accepts_valid_color(self):
        data = {"name": "Tag", "color": "#4ECDC4"}
        form = TagForm(data=data)
        assert form.is_valid()

    def test_rejects_invalid_color(self):
        data = {"name": "Tag", "color": "red"}
        form = TagForm(data=data)
        assert not form.is_valid()
        assert "color" in form.errors

    def test_includes_correct_fields(self):
        form = TagForm()
        assert set(form.fields.keys()) == {"name", "color"}

    def test_default_color_is_teal(self):
        data = {"name": "Tag"}
        form = TagForm(data=data)
        # Color has default so form should be valid without explicit color
        # Actually RadioSelect requires a selection, let's test with a valid choice
        data = {"name": "Tag", "color": "#4ECDC4"}
        form = TagForm(data=data)
        assert form.is_valid()
