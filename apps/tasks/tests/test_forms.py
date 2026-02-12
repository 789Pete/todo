import pytest

from apps.tasks.forms import TaskForm


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
        expected_fields = {"title", "description", "status", "priority", "due_date"}
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
