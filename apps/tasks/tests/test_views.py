import json
from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.tasks.models import Tag, Task
from apps.tasks.tests.factories import TagFactory, TaskFactory


@pytest.mark.django_db
class TestTaskListView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("task-list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_shows_only_current_users_tasks(self):
        user = UserFactory()
        other_user = UserFactory()
        task = TaskFactory(user=user)
        TaskFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list"))

        assert response.status_code == 200
        tasks = list(response.context["tasks"])
        assert len(tasks) == 1
        assert task in tasks

    def test_pagination_works(self):
        user = UserFactory()
        TaskFactory.create_batch(30, user=user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list"))

        assert response.status_code == 200
        assert response.context["is_paginated"]
        assert len(response.context["tasks"]) == 25

        response_p2 = client.get(reverse("task-list") + "?page=2")
        assert len(response_p2.context["tasks"]) == 5

    def test_sort_by_priority(self):
        user = UserFactory()
        TaskFactory(user=user, priority="low")
        TaskFactory(user=user, priority="high")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?sort=priority")

        tasks = list(response.context["tasks"])
        assert tasks[0].priority == "high"
        assert tasks[1].priority == "low"

    def test_sort_by_due_date(self):
        user = UserFactory()
        later = TaskFactory(user=user, due_date=date.today() + timedelta(days=10))
        sooner = TaskFactory(user=user, due_date=date.today() + timedelta(days=1))

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?sort=due_date")

        tasks = list(response.context["tasks"])
        assert tasks[0] == sooner
        assert tasks[1] == later

    def test_filter_by_status(self):
        user = UserFactory()
        todo_task = TaskFactory(user=user, status="todo")
        done_task = TaskFactory(user=user, status="done")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?status=todo")

        tasks = list(response.context["tasks"])
        assert len(tasks) == 1
        assert todo_task in tasks
        assert done_task not in tasks

    def test_empty_state(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list"))

        assert response.status_code == 200
        assert len(response.context["tasks"]) == 0


@pytest.mark.django_db
class TestTaskDetailView:
    def test_requires_authentication(self, client):
        task = TaskFactory()
        response = client.get(reverse("task-detail", kwargs={"pk": task.pk}))
        assert response.status_code == 302
        assert "login" in response.url

    def test_shows_task_info(self):
        user = UserFactory()
        task = TaskFactory(user=user, title="Test Task Detail")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-detail", kwargs={"pk": task.pk}))

        assert response.status_code == 200
        assert response.context["task"] == task
        assert "Test Task Detail" in response.content.decode()

    def test_returns_404_for_other_users_task(self):
        user = UserFactory()
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-detail", kwargs={"pk": task.pk}))

        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskCreateView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("task-create"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_shows_empty_form(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-create"))

        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_data_creates_task(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {
            "title": "New Task",
            "description": "A description",
            "status": "todo",
            "priority": "high",
        }
        response = client.post(reverse("task-create"), data)

        assert response.status_code == 302
        assert Task.objects.filter(user=user, title="New Task").exists()

    def test_post_assigns_task_to_logged_in_user(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {
            "title": "User Task",
            "status": "todo",
            "priority": "medium",
        }
        client.post(reverse("task-create"), data)

        task = Task.objects.get(title="User Task")
        assert task.user == user

    def test_post_invalid_data_shows_form_errors(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {
            "title": "",
            "status": "todo",
            "priority": "medium",
        }
        response = client.post(reverse("task-create"), data)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].errors

    def test_post_shows_success_message(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {
            "title": "Message Task",
            "status": "todo",
            "priority": "medium",
        }
        response = client.post(reverse("task-create"), data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "created successfully" in str(messages[0])


@pytest.mark.django_db
class TestTaskUpdateView:
    def test_requires_authentication(self, client):
        task = TaskFactory()
        response = client.get(reverse("task-update", kwargs={"pk": task.pk}))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_prepopulates_form(self):
        user = UserFactory()
        task = TaskFactory(user=user, title="Original Title")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-update", kwargs={"pk": task.pk}))

        assert response.status_code == 200
        assert response.context["form"].initial["title"] == "Original Title"

    def test_post_valid_data_updates_task(self):
        user = UserFactory()
        task = TaskFactory(user=user, title="Old Title")

        client = Client()
        client.force_login(user)

        data = {
            "title": "Updated Title",
            "description": task.description,
            "status": "in_progress",
            "priority": task.priority,
        }
        response = client.post(reverse("task-update", kwargs={"pk": task.pk}), data)

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.title == "Updated Title"
        assert task.status == "in_progress"

    def test_returns_404_for_other_users_task(self):
        user = UserFactory()
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-update", kwargs={"pk": task.pk}))

        assert response.status_code == 404

    def test_post_shows_success_message(self):
        user = UserFactory()
        task = TaskFactory(user=user)

        client = Client()
        client.force_login(user)

        data = {
            "title": "Updated",
            "description": "",
            "status": "todo",
            "priority": "medium",
        }
        response = client.post(
            reverse("task-update", kwargs={"pk": task.pk}), data, follow=True
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "updated successfully" in str(messages[0])


@pytest.mark.django_db
class TestTaskDeleteView:
    def test_requires_authentication(self, client):
        task = TaskFactory()
        response = client.get(reverse("task-delete", kwargs={"pk": task.pk}))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_shows_confirmation_page(self):
        user = UserFactory()
        task = TaskFactory(user=user, title="Delete Me")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-delete", kwargs={"pk": task.pk}))

        assert response.status_code == 200
        assert "Delete Me" in response.content.decode()

    def test_post_deletes_task_and_redirects(self):
        user = UserFactory()
        task = TaskFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-delete", kwargs={"pk": task.pk}))

        assert response.status_code == 302
        assert not Task.objects.filter(pk=task.pk).exists()

    def test_returns_404_for_other_users_task(self):
        user = UserFactory()
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-delete", kwargs={"pk": task.pk}))

        assert response.status_code == 404

    def test_post_shows_success_message(self):
        user = UserFactory()
        task = TaskFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("task-delete", kwargs={"pk": task.pk}), follow=True
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "deleted successfully" in str(messages[0])


@pytest.mark.django_db
class TestTaskToggleStatusView:
    def test_toggle_requires_authentication(self, client):
        task = TaskFactory()
        url = reverse("task-toggle-status", kwargs={"pk": task.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_toggle_returns_404_for_other_users_task(self):
        user = UserFactory()
        other_user = UserFactory()
        task = TaskFactory(user=other_user, status="todo")

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-toggle-status", kwargs={"pk": task.pk}))
        assert response.status_code == 404

    def test_toggle_get_request_rejected(self):
        user = UserFactory()
        task = TaskFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-toggle-status", kwargs={"pk": task.pk}))
        assert response.status_code == 405

    def test_toggle_todo_to_done(self):
        user = UserFactory()
        task = TaskFactory(user=user, status="todo")

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-toggle-status", kwargs={"pk": task.pk}))

        task.refresh_from_db()
        assert task.status == "done"
        assert task.completed_at is not None
        assert response.status_code == 302

    def test_toggle_done_to_todo(self):
        user = UserFactory()
        task = TaskFactory(user=user, status="todo")
        task.mark_complete()

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-toggle-status", kwargs={"pk": task.pk}))

        task.refresh_from_db()
        assert task.status == "todo"
        assert task.completed_at is None
        assert response.status_code == 302

    def test_toggle_shows_success_message_on_complete(self):
        user = UserFactory()
        task = TaskFactory(user=user, status="todo", title="My Task")

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("task-toggle-status", kwargs={"pk": task.pk}), follow=True
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "marked as complete" in str(messages[0])

    def test_toggle_redirects_to_task_list(self):
        user = UserFactory()
        task = TaskFactory(user=user, status="todo")

        client = Client()
        client.force_login(user)
        response = client.post(reverse("task-toggle-status", kwargs={"pk": task.pk}))

        assert response.status_code == 302
        assert response.url == reverse("task-list")


@pytest.mark.django_db
class TestTaskListViewFilterSort:
    def test_active_filter_returns_only_non_done_tasks(self):
        user = UserFactory()
        todo_task = TaskFactory(user=user, status="todo")
        ip_task = TaskFactory(user=user, status="in_progress")
        TaskFactory(user=user, status="done")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?status=active")

        tasks = list(response.context["tasks"])
        assert len(tasks) == 2
        assert todo_task in tasks
        assert ip_task in tasks

    def test_default_ordering_high_priority_first(self):
        user = UserFactory()
        low = TaskFactory(user=user, priority="low")
        high = TaskFactory(user=user, priority="high")
        medium = TaskFactory(user=user, priority="medium")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list"))

        tasks = list(response.context["tasks"])
        assert tasks[0] == high
        assert tasks[1] == medium
        assert tasks[2] == low

    def test_explicit_sort_overrides_default_priority(self):
        user = UserFactory()
        TaskFactory(user=user, priority="high")
        TaskFactory(user=user, priority="low")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?sort=-created_at")

        # Should not error; explicit sort takes precedence
        assert response.status_code == 200


# --- Tag View Tests ---


@pytest.mark.django_db
class TestTagListView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("tag-list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_shows_only_current_users_tags(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=user)
        TagFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-list"))

        assert response.status_code == 200
        tags = list(response.context["tags"])
        assert len(tags) == 1
        assert tags[0].pk == tag.pk

    def test_includes_task_count_annotation(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])
        TaskFactory(user=user, tags=[tag])

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-list"))

        tags = list(response.context["tags"])
        assert tags[0].num_tasks == 2

    def test_includes_color_choices_in_context(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-list"))

        assert "color_choices" in response.context
        assert response.context["color_choices"] == Tag.COLOR_CHOICES

    def test_tags_ordered_by_name(self):
        user = UserFactory()
        TagFactory(user=user, name="Zebra")
        TagFactory(user=user, name="Alpha")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-list"))

        tags = list(response.context["tags"])
        assert tags[0].name == "Alpha"
        assert tags[1].name == "Zebra"


@pytest.mark.django_db
class TestTagCreateView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("tag-create"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_shows_form(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-create"))

        assert response.status_code == 200
        assert "form" in response.context

    def test_post_valid_data_creates_tag(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {"name": "Work", "color": "#FF6B6B"}
        response = client.post(reverse("tag-create"), data)

        assert response.status_code == 302
        assert Tag.objects.filter(user=user, name="Work").exists()

    def test_post_assigns_tag_to_logged_in_user(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {"name": "Personal", "color": "#4ECDC4"}
        client.post(reverse("tag-create"), data)

        tag = Tag.objects.get(name="Personal")
        assert tag.user == user

    def test_post_shows_success_message(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {"name": "Urgent", "color": "#FF6B6B"}
        response = client.post(reverse("tag-create"), data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "created successfully" in str(messages[0])

    def test_rejects_duplicate_tag_name_case_insensitive(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")

        client = Client()
        client.force_login(user)

        data = {"name": "work", "color": "#4ECDC4"}
        response = client.post(reverse("tag-create"), data)

        assert response.status_code == 200
        assert response.context["form"].errors

    def test_redirects_to_tag_list_on_success(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {"name": "New Tag", "color": "#45B7D1"}
        response = client.post(reverse("tag-create"), data)

        assert response.status_code == 302
        assert response.url == reverse("tag-list")


@pytest.mark.django_db
class TestTagUpdateView:
    def test_requires_authentication(self, client):
        tag = TagFactory()
        response = client.get(reverse("tag-update", kwargs={"pk": tag.pk}))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_prepopulates_form(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Original")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-update", kwargs={"pk": tag.pk}))

        assert response.status_code == 200
        assert response.context["form"].initial["name"] == "Original"

    def test_post_valid_data_updates_tag(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Old Name", color="#FF6B6B")

        client = Client()
        client.force_login(user)

        data = {"name": "New Name", "color": "#4ECDC4"}
        response = client.post(reverse("tag-update", kwargs={"pk": tag.pk}), data)

        assert response.status_code == 302
        tag.refresh_from_db()
        assert tag.name == "New Name"
        assert tag.color == "#4ECDC4"

    def test_returns_404_for_other_users_tag(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-update", kwargs={"pk": tag.pk}))

        assert response.status_code == 404

    def test_post_shows_success_message(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)

        data = {"name": "Updated", "color": "#FF6B6B"}
        response = client.post(
            reverse("tag-update", kwargs={"pk": tag.pk}), data, follow=True
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "updated successfully" in str(messages[0])

    def test_rejects_rename_to_existing_name_case_insensitive(self):
        user = UserFactory()
        TagFactory(user=user, name="Existing")
        tag = TagFactory(user=user, name="Other")

        client = Client()
        client.force_login(user)

        data = {"name": "existing", "color": "#FF6B6B"}
        response = client.post(reverse("tag-update", kwargs={"pk": tag.pk}), data)

        assert response.status_code == 200
        assert response.context["form"].errors


@pytest.mark.django_db
class TestTagDeleteView:
    def test_requires_authentication(self, client):
        tag = TagFactory()
        response = client.get(reverse("tag-delete", kwargs={"pk": tag.pk}))
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_shows_confirmation_page(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Delete Me")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-delete", kwargs={"pk": tag.pk}))

        assert response.status_code == 200
        assert "Delete Me" in response.content.decode()

    def test_shows_task_count_in_context(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-delete", kwargs={"pk": tag.pk}))

        assert response.context["task_count"] == 1

    def test_post_deletes_tag_and_redirects(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(reverse("tag-delete", kwargs={"pk": tag.pk}))

        assert response.status_code == 302
        assert not Tag.objects.filter(pk=tag.pk).exists()

    def test_returns_404_for_other_users_tag(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=other_user)

        client = Client()
        client.force_login(user)
        response = client.post(reverse("tag-delete", kwargs={"pk": tag.pk}))

        assert response.status_code == 404

    def test_post_shows_success_message(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-delete", kwargs={"pk": tag.pk}), follow=True
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "deleted successfully" in str(messages[0])

    def test_deleting_tag_does_not_delete_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user, tags=[tag])

        client = Client()
        client.force_login(user)
        client.post(reverse("tag-delete", kwargs={"pk": tag.pk}))

        assert Task.objects.filter(pk=task.pk).exists()


@pytest.mark.django_db
class TestTagQuickCreateView:
    def test_requires_authentication(self, client):
        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 302

    def test_creates_tag_and_returns_json(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": "QuickTag"}),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "QuickTag"
        assert "id" in data
        assert "color" in data
        assert Tag.objects.filter(user=user, name="QuickTag").exists()

    def test_rejects_empty_name(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": ""}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_rejects_whitespace_only_name(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": "   "}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_rejects_duplicate_name_case_insensitive(self):
        user = UserFactory()
        TagFactory(user=user, name="Existing")

        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": "existing"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_rejects_invalid_json(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            "not json",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_auto_assigns_color(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-quick-create"),
            json.dumps({"name": "AutoColor"}),
            content_type="application/json",
        )

        data = response.json()
        valid_colors = [c[0] for c in Tag.COLOR_CHOICES]
        assert data["color"] in valid_colors

    def test_get_request_rejected(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.get(reverse("tag-quick-create"))
        assert response.status_code == 405


@pytest.mark.django_db
class TestTagAutocompleteView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("tag-autocomplete"))
        assert response.status_code == 302

    def test_returns_user_tags_as_json(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")
        TagFactory(user=user, name="Personal")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete"))

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filters_by_query(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")
        TagFactory(user=user, name="Personal")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete") + "?q=wor")

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Work"

    def test_case_insensitive_search(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete") + "?q=WORK")

        data = response.json()
        assert len(data) == 1

    def test_does_not_return_other_users_tags(self):
        user = UserFactory()
        other_user = UserFactory()
        TagFactory(user=user, name="Mine")
        TagFactory(user=other_user, name="Theirs")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete"))

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Mine"

    def test_limits_to_10_results(self):
        user = UserFactory()
        TagFactory.create_batch(15, user=user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete"))

        data = response.json()
        assert len(data) == 10

    def test_returns_tag_id_name_color(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Test", color="#FF6B6B")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-autocomplete"))

        data = response.json()
        assert data[0]["id"] == str(tag.pk)
        assert data[0]["name"] == "Test"
        assert data[0]["color"] == "#FF6B6B"


@pytest.mark.django_db
class TestTagBulkEditView:
    def test_requires_authentication(self, client):
        response = client.post(reverse("tag-bulk-edit"))
        assert response.status_code == 302

    def test_bulk_delete_tags(self):
        user = UserFactory()
        tags = TagFactory.create_batch(3, user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(t.pk) for t in tags], "bulk_action": "delete"},
        )

        assert response.status_code == 302
        assert Tag.objects.filter(user=user).count() == 0

    def test_bulk_change_color(self):
        user = UserFactory()
        tags = TagFactory.create_batch(2, user=user, color="#FF6B6B")

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(t.pk) for t in tags], "bulk_action": "color:#4ECDC4"},
        )

        assert response.status_code == 302
        for t in tags:
            t.refresh_from_db()
            assert t.color == "#4ECDC4"

    def test_rejects_invalid_color(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(tag.pk)], "bulk_action": "color:#INVALID"},
            follow=True,
        )

        messages = list(response.context["messages"])
        assert any("Invalid color" in str(m) for m in messages)

    def test_no_tags_selected_shows_warning(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [], "bulk_action": "delete"},
            follow=True,
        )

        messages = list(response.context["messages"])
        assert any("No tags selected" in str(m) for m in messages)

    def test_cannot_bulk_edit_other_users_tags(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=other_user, color="#FF6B6B")

        client = Client()
        client.force_login(user)
        client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(tag.pk)], "bulk_action": "delete"},
        )

        # Tag should still exist - user can't delete others' tags
        assert Tag.objects.filter(pk=tag.pk).exists()

    def test_no_action_selected_shows_warning(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(tag.pk)], "bulk_action": ""},
            follow=True,
        )

        messages = list(response.context["messages"])
        assert any("No action selected" in str(m) for m in messages)

    def test_bulk_delete_shows_success_message(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-bulk-edit"),
            {"tag_ids": [str(tag.pk)], "bulk_action": "delete"},
            follow=True,
        )

        messages = list(response.context["messages"])
        assert any("Deleted" in str(m) for m in messages)


@pytest.mark.django_db
class TestTaskCreateWithTags:
    def test_create_task_with_tags(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        data = {
            "title": "Tagged Task",
            "status": "todo",
            "priority": "medium",
            "tags": [str(tag.pk)],
        }
        response = client.post(reverse("task-create"), data)

        assert response.status_code == 302
        task = Task.objects.get(title="Tagged Task")
        assert tag in task.tags.all()

    def test_create_task_without_tags(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        data = {
            "title": "No Tags",
            "status": "todo",
            "priority": "medium",
        }
        response = client.post(reverse("task-create"), data)

        assert response.status_code == 302
        task = Task.objects.get(title="No Tags")
        assert task.tags.count() == 0

    def test_form_shows_only_users_tags(self):
        user = UserFactory()
        other_user = UserFactory()
        TagFactory(user=user, name="MyTag")
        TagFactory(user=other_user, name="OtherTag")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-create"))

        form = response.context["form"]
        tag_names = list(form.fields["tags"].queryset.values_list("name", flat=True))
        assert "MyTag" in tag_names
        assert "OtherTag" not in tag_names


@pytest.mark.django_db
class TestTaskUpdateWithTags:
    def test_update_task_add_tags(self):
        user = UserFactory()
        task = TaskFactory(user=user)
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        data = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "tags": [str(tag.pk)],
        }
        response = client.post(reverse("task-update", kwargs={"pk": task.pk}), data)

        assert response.status_code == 302
        task.refresh_from_db()
        assert tag in task.tags.all()

    def test_update_task_remove_tags(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user, tags=[tag])

        client = Client()
        client.force_login(user)
        data = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            # No tags submitted = remove all
        }
        response = client.post(reverse("task-update", kwargs={"pk": task.pk}), data)

        assert response.status_code == 302
        task.refresh_from_db()
        assert task.tags.count() == 0
