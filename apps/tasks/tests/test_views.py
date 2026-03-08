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

    def test_task_detail_with_from_graph_param(self, client):
        user = UserFactory()
        task = TaskFactory(user=user)
        client.force_login(user)
        url = reverse("task-detail", kwargs={"pk": task.pk}) + "?from_graph=1"
        response = client.get(url)
        assert response.status_code == 200
        assert b"/visualization/" in response.content  # graph-view URL rendered
        assert b"Back to Graph" in response.content


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

    def test_task_list_contains_graph_view_link(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert response.status_code == 200
        assert b"Graph View" in response.content


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


@pytest.mark.django_db
class TestTagColorUpdateView:
    def test_requires_authentication(self, client):
        tag = TagFactory()
        response = client.post(
            reverse("tag-color-update", kwargs={"pk": tag.pk}),
            json.dumps({"color": "#4ECDC4"}),
            content_type="application/json",
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_updates_color_and_returns_json(self):
        user = UserFactory()
        tag = TagFactory(user=user, color="#FF6B6B")

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-color-update", kwargs={"pk": tag.pk}),
            json.dumps({"color": "#4ECDC4"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["color"] == "#4ECDC4"
        tag.refresh_from_db()
        assert tag.color == "#4ECDC4"

    def test_rejects_invalid_color(self):
        user = UserFactory()
        tag = TagFactory(user=user, color="#FF6B6B")

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-color-update", kwargs={"pk": tag.pk}),
            json.dumps({"color": "#BADCOL"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "error" in response.json()
        tag.refresh_from_db()
        assert tag.color == "#FF6B6B"  # unchanged

    def test_returns_404_for_other_users_tag(self):
        user = UserFactory()
        other_user = UserFactory()
        tag = TagFactory(user=other_user, color="#FF6B6B")

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-color-update", kwargs={"pk": tag.pk}),
            json.dumps({"color": "#4ECDC4"}),
            content_type="application/json",
        )

        assert response.status_code == 404
        tag.refresh_from_db()
        assert tag.color == "#FF6B6B"  # unchanged

    def test_get_request_rejected(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-color-update", kwargs={"pk": tag.pk}))
        assert response.status_code == 405

    def test_rejects_invalid_json(self):
        user = UserFactory()
        tag = TagFactory(user=user)

        client = Client()
        client.force_login(user)
        response = client.post(
            reverse("tag-color-update", kwargs={"pk": tag.pk}),
            "not json",
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestTagExportView:
    def test_requires_authentication(self, client):
        response = client.get(reverse("tag-export"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_returns_csv_with_correct_headers(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.get(reverse("tag-export"))

        assert response.status_code == 200
        assert "text/csv" in response["Content-Type"]
        assert "attachment" in response["Content-Disposition"]
        assert "tags.csv" in response["Content-Disposition"]

    def test_csv_contains_correct_columns(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.get(reverse("tag-export"))
        content = response.content.decode("utf-8")
        lines = content.strip().splitlines()

        assert lines[0] == "name,color,task_count,created_at"

    def test_csv_contains_user_tag_data(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Work", color="#4ECDC4")
        task = TaskFactory(user=user)
        task.tags.add(tag)

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-export"))

        content = response.content.decode("utf-8")
        assert "Work" in content
        assert "#4ECDC4" in content
        assert ",1," in content  # task_count = 1

    def test_only_exports_current_users_tags(self):
        user = UserFactory()
        other_user = UserFactory()
        TagFactory(user=user, name="MyTag")
        TagFactory(user=other_user, name="OtherTag")

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-export"))

        content = response.content.decode("utf-8")
        assert "MyTag" in content
        assert "OtherTag" not in content

    def test_task_count_is_correct(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="MultiTask")
        TaskFactory(user=user, tags=[tag])
        TaskFactory(user=user, tags=[tag])
        TaskFactory(user=user, tags=[tag])

        client = Client()
        client.force_login(user)
        response = client.get(reverse("tag-export"))

        content = response.content.decode("utf-8")
        # Row: MultiTask,#color,3,datetime
        assert "MultiTask" in content
        lines = [row for row in content.strip().splitlines() if "MultiTask" in row]
        assert len(lines) == 1
        parts = lines[0].split(",")
        assert parts[2] == "3"

    def test_empty_export_has_only_header(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.get(reverse("tag-export"))

        content = response.content.decode("utf-8")
        lines = content.strip().splitlines()
        assert len(lines) == 1  # just the header row

    def test_post_request_rejected(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)

        response = client.post(reverse("tag-export"))
        assert response.status_code == 405


@pytest.mark.django_db
class TestTaskListViewTagFilter:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_single_tag_filter_returns_only_matching_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task_with = TaskFactory(user=user, tags=[tag])
        task_without = TaskFactory(user=user)

        response = self._client(user).get(reverse("task-list") + f"?tags={tag.pk}")

        tasks = list(response.context["tasks"])
        assert task_with in tasks
        assert task_without not in tasks

    def test_and_mode_returns_only_tasks_with_all_tags(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag2 = TagFactory(user=user)
        task_both = TaskFactory(user=user, tags=[tag1, tag2])
        task_one = TaskFactory(user=user, tags=[tag1])
        task_none = TaskFactory(user=user)

        response = self._client(user).get(
            reverse("task-list") + f"?tags={tag1.pk}&tags={tag2.pk}&tag_mode=and"
        )

        tasks = list(response.context["tasks"])
        assert task_both in tasks
        assert task_one not in tasks
        assert task_none not in tasks

    def test_or_mode_returns_tasks_with_any_tag(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag2 = TagFactory(user=user)
        task_tag1 = TaskFactory(user=user, tags=[tag1])
        task_tag2 = TaskFactory(user=user, tags=[tag2])
        task_none = TaskFactory(user=user)

        response = self._client(user).get(
            reverse("task-list") + f"?tags={tag1.pk}&tags={tag2.pk}&tag_mode=or"
        )

        tasks = list(response.context["tasks"])
        assert task_tag1 in tasks
        assert task_tag2 in tasks
        assert task_none not in tasks

    def test_tag_filter_combined_with_status_filter(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task_todo = TaskFactory(user=user, status="todo", tags=[tag])
        task_done = TaskFactory(user=user, status="done", tags=[tag])

        response = self._client(user).get(
            reverse("task-list") + f"?tags={tag.pk}&status=todo"
        )

        tasks = list(response.context["tasks"])
        assert task_todo in tasks
        assert task_done not in tasks

    def test_tag_filter_combined_with_sort_param(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task_high = TaskFactory(user=user, priority="high", tags=[tag])
        task_low = TaskFactory(user=user, priority="low", tags=[tag])

        # sort=priority sorts ascending alphabetically: "high" < "low"
        response = self._client(user).get(
            reverse("task-list") + f"?tags={tag.pk}&sort=priority"
        )

        tasks = list(response.context["tasks"])
        assert tasks[0] == task_high
        assert tasks[1] == task_low

    def test_invalid_tag_uuid_in_filter_is_ignored(self):
        user = UserFactory()
        response = self._client(user).get(
            reverse("task-list") + "?tags=00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 200

    def test_other_users_tag_uuid_is_ignored(self):
        user = UserFactory()
        other_user = UserFactory()
        other_tag = TagFactory(user=other_user)
        TaskFactory(user=user)

        response = self._client(user).get(
            reverse("task-list") + f"?tags={other_tag.pk}"
        )

        # No 500 error, task is not filtered out (other user's tag ignored in context)
        assert response.status_code == 200
        # active_tags only shows user-scoped tags
        assert other_tag not in list(response.context["active_tags"])

    def test_active_tags_context_contains_correct_tags(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag2 = TagFactory(user=user)

        response = self._client(user).get(
            reverse("task-list") + f"?tags={tag1.pk}&tags={tag2.pk}"
        )

        active_tags = list(response.context["active_tags"])
        assert tag1 in active_tags
        assert tag2 in active_tags

    def test_result_count_context_reflects_filtered_count(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])
        TaskFactory(user=user, tags=[tag])
        TaskFactory(user=user)  # not tagged

        response = self._client(user).get(reverse("task-list") + f"?tags={tag.pk}")

        assert response.context["result_count"] == 2
        assert response.context["any_filter_active"] is True

    def test_tag_mode_defaults_to_and(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])

        response = self._client(user).get(reverse("task-list") + f"?tags={tag.pk}")

        assert response.context["tag_mode"] == "and"

    def test_no_tag_filter_returns_all_user_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task1 = TaskFactory(user=user, tags=[tag])
        task2 = TaskFactory(user=user)

        response = self._client(user).get(reverse("task-list"))

        tasks = list(response.context["tasks"])
        assert task1 in tasks
        assert task2 in tasks


# ---------------------------------------------------------------------------
# Story 2.5: Tag Management Interface
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTagListViewSort:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_default_sort_is_name_ascending(self):
        user = UserFactory()
        TagFactory(user=user, name="Zebra")
        TagFactory(user=user, name="Alpha")
        TagFactory(user=user, name="Middle")

        response = self._client(user).get(reverse("tag-list"))

        tags = list(response.context["tags"])
        names = [t.name for t in tags]
        assert names == sorted(names)

    def test_sort_by_num_tasks_ascending(self):
        user = UserFactory()
        tag_many = TagFactory(user=user, name="Many")
        TagFactory(user=user, name="Few")
        TaskFactory(user=user, tags=[tag_many])
        TaskFactory(user=user, tags=[tag_many])

        response = self._client(user).get(reverse("tag-list") + "?sort=num_tasks")

        tags = list(response.context["tags"])
        counts = [t.num_tasks for t in tags]
        assert counts == sorted(counts)
        assert tags[-1].pk == tag_many.pk

    def test_sort_by_num_tasks_descending(self):
        user = UserFactory()
        tag_many = TagFactory(user=user, name="Many")
        TagFactory(user=user, name="Few")
        TaskFactory(user=user, tags=[tag_many])
        TaskFactory(user=user, tags=[tag_many])

        response = self._client(user).get(reverse("tag-list") + "?sort=-num_tasks")

        tags = list(response.context["tags"])
        assert tags[0].pk == tag_many.pk

    def test_sort_by_created_at_ascending(self):
        user = UserFactory()
        TagFactory(user=user, name="A")
        TagFactory(user=user, name="B")

        response = self._client(user).get(reverse("tag-list") + "?sort=created_at")

        tags = list(response.context["tags"])
        created_ats = [t.created_at for t in tags]
        assert created_ats == sorted(created_ats)

    def test_invalid_sort_falls_back_to_name(self):
        user = UserFactory()
        TagFactory(user=user, name="Zebra")
        TagFactory(user=user, name="Alpha")

        response = self._client(user).get(reverse("tag-list") + "?sort=invalid")

        tags = list(response.context["tags"])
        names = [t.name for t in tags]
        assert names == sorted(names)


@pytest.mark.django_db
class TestTagListViewSearch:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_search_returns_matching_tags_case_insensitive(self):
        user = UserFactory()
        TagFactory(user=user, name="FooBar")
        TagFactory(user=user, name="Baz")

        response = self._client(user).get(reverse("tag-list") + "?q=foo")

        tags = list(response.context["tags"])
        assert len(tags) == 1
        assert tags[0].name == "FooBar"

    def test_empty_search_returns_all_tags(self):
        user = UserFactory()
        TagFactory(user=user, name="Alpha")
        TagFactory(user=user, name="Beta")

        response = self._client(user).get(reverse("tag-list") + "?q=")

        assert response.context["tags"].count() == 2

    def test_other_users_tags_never_returned(self):
        user = UserFactory()
        other = UserFactory()
        TagFactory(user=other, name="foo")

        response = self._client(user).get(reverse("tag-list") + "?q=foo")

        assert response.context["tags"].count() == 0


@pytest.mark.django_db
class TestTagListViewUnused:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_show_unused_returns_only_unused_tags(self):
        user = UserFactory()
        used = TagFactory(user=user, name="Used")
        unused = TagFactory(user=user, name="Unused")
        TaskFactory(user=user, tags=[used])

        response = self._client(user).get(reverse("tag-list") + "?show_unused=1")

        tags = list(response.context["tags"])
        assert len(tags) == 1
        assert tags[0].pk == unused.pk

    def test_without_param_returns_all_tags(self):
        user = UserFactory()
        used = TagFactory(user=user, name="Used")
        unused = TagFactory(user=user, name="Unused")
        TaskFactory(user=user, tags=[used])

        response = self._client(user).get(reverse("tag-list"))

        pks = [t.pk for t in response.context["tags"]]
        assert used.pk in pks
        assert unused.pk in pks


@pytest.mark.django_db
class TestTagNameUpdateView:
    def _url(self, tag):
        return reverse("tag-name-update", kwargs={"pk": tag.pk})

    def test_requires_authentication(self, client):
        tag = TagFactory()
        response = client.post(
            self._url(tag),
            data=json.dumps({"name": "x"}),
            content_type="application/json",
        )
        assert response.status_code == 302

    def test_rename_success(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Old")
        c = Client()
        c.force_login(user)

        response = c.post(
            self._url(tag),
            data=json.dumps({"name": "New"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New"
        tag.refresh_from_db()
        assert tag.name == "New"

    def test_rejects_empty_name(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        c = Client()
        c.force_login(user)

        response = c.post(
            self._url(tag),
            data=json.dumps({"name": "  "}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_rejects_duplicate_name_case_insensitive(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")
        tag = TagFactory(user=user, name="Personal")
        c = Client()
        c.force_login(user)

        response = c.post(
            self._url(tag),
            data=json.dumps({"name": "work"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_allows_rename_to_same_name_idempotent(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Work")
        c = Client()
        c.force_login(user)

        response = c.post(
            self._url(tag),
            data=json.dumps({"name": "Work"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Work"

    def test_returns_404_for_other_users_tag(self):
        user = UserFactory()
        other_tag = TagFactory()
        c = Client()
        c.force_login(user)

        response = c.post(
            self._url(other_tag),
            data=json.dumps({"name": "x"}),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_rejects_get_request(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        c = Client()
        c.force_login(user)

        response = c.get(self._url(tag))

        assert response.status_code == 405


@pytest.mark.django_db
class TestTagMergeView:
    def _url(self, tag):
        return reverse("tag-merge", kwargs={"pk": tag.pk})

    def test_requires_authentication(self, client):
        tag = TagFactory()
        response = client.get(self._url(tag))
        assert response.status_code == 302

    def test_get_renders_form_with_source_and_other_tags(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag2 = TagFactory(user=user)
        c = Client()
        c.force_login(user)

        response = c.get(self._url(tag1))

        assert response.status_code == 200
        assert response.context["source_tag"] == tag1
        assert tag2 in response.context["other_tags"]

    def test_get_returns_404_for_other_users_source_tag(self):
        user = UserFactory()
        other_tag = TagFactory()
        c = Client()
        c.force_login(user)

        response = c.get(self._url(other_tag))

        assert response.status_code == 404

    def test_post_reassigns_tasks_to_target_and_deletes_source(self):
        user = UserFactory()
        source = TagFactory(user=user)
        target = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(source)
        c = Client()
        c.force_login(user)

        response = c.post(self._url(source), {"target_tag": str(target.pk)})

        assert response.status_code == 302
        assert not Tag.objects.filter(pk=source.pk).exists()
        task.refresh_from_db()
        assert target in task.tags.all()

    def test_post_merge_with_self_redirects_with_error_does_not_delete(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        c = Client()
        c.force_login(user)

        response = c.post(self._url(tag), {"target_tag": str(tag.pk)})

        assert response.status_code == 302
        assert Tag.objects.filter(pk=tag.pk).exists()

    def test_post_rejects_target_from_other_user(self):
        user = UserFactory()
        source = TagFactory(user=user)
        other_target = TagFactory()
        c = Client()
        c.force_login(user)

        response = c.post(self._url(source), {"target_tag": str(other_target.pk)})

        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskListViewPopularTags:
    def test_popular_tags_in_context(self, client):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert response.status_code == 200
        assert "popular_tags" in response.context

    def test_popular_tags_ordered_by_task_count_desc(self, client):
        user = UserFactory()
        tag_high = TagFactory(user=user)
        tag_low = TagFactory(user=user)
        TaskFactory.create_batch(3, user=user, tags=[tag_high])
        task = TaskFactory(user=user)
        task.tags.add(tag_low)
        client.force_login(user)
        response = client.get(reverse("task-list"))
        popular = list(response.context["popular_tags"])
        assert popular[0] == tag_high
        assert popular[1] == tag_low

    def test_popular_tags_limited_to_5(self, client):
        user = UserFactory()
        for _ in range(7):
            tag = TagFactory(user=user)
            task = TaskFactory(user=user)
            task.tags.add(tag)
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert len(list(response.context["popular_tags"])) <= 5

    def test_popular_tags_excludes_unused_tags(self, client):
        user = UserFactory()
        TagFactory(user=user)  # unused tag
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert len(list(response.context["popular_tags"])) == 0

    def test_popular_tags_excludes_other_users_tags(self, client):
        user = UserFactory()
        other_tag = TagFactory()  # different user
        other_task = TaskFactory(user=other_tag.user)
        other_task.tags.add(other_tag)
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert other_tag not in list(response.context["popular_tags"])


@pytest.mark.django_db
class TestTaskListViewBreadcrumb:
    def test_no_active_tags_when_no_filter(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("task-list"))
        assert len(list(response.context["active_tags"])) == 0

    def test_active_tags_in_context_when_filtered(self, client):
        user = UserFactory()
        tag = TagFactory(user=user)
        client.force_login(user)
        url = reverse("task-list") + f"?tags={tag.pk}"
        response = client.get(url)
        assert tag in response.context["active_tags"]

    def test_tag_remove_url_exists_for_active_tag(self, client):
        user = UserFactory()
        tag = TagFactory(user=user)
        client.force_login(user)
        url = reverse("task-list") + f"?tags={tag.pk}"
        response = client.get(url)
        remove_urls = response.context["tag_remove_urls"]
        assert str(tag.pk) in remove_urls
        assert isinstance(remove_urls[str(tag.pk)], str)


@pytest.mark.django_db
class TestTaskListSearch:
    def test_search_filters_by_title(self, client):
        user = UserFactory()
        TaskFactory(user=user, title="Write documentation")
        TaskFactory(user=user, title="Fix bug in login")
        TaskFactory(user=user, title="Write unit tests")
        client.force_login(user)
        response = client.get(reverse("task-list") + "?q=write")
        tasks = list(response.context["tasks"])
        assert len(tasks) == 2
        assert all("write" in t.title.lower() for t in tasks)

    def test_search_is_case_insensitive(self, client):
        user = UserFactory()
        TaskFactory(user=user, title="Django Tutorial")
        client.force_login(user)
        response = client.get(reverse("task-list") + "?q=django")
        assert len(list(response.context["tasks"])) == 1

    def test_search_combines_with_status_filter(self, client):
        user = UserFactory()
        TaskFactory(user=user, title="Write docs", status="todo")
        TaskFactory(user=user, title="Write tests", status="done")
        client.force_login(user)
        response = client.get(reverse("task-list") + "?q=write&status=done")
        tasks = list(response.context["tasks"])
        assert len(tasks) == 1
        assert tasks[0].title == "Write tests"

    def test_empty_search_returns_all_tasks(self, client):
        user = UserFactory()
        TaskFactory.create_batch(3, user=user)
        client.force_login(user)
        response = client.get(reverse("task-list") + "?q=")
        assert len(list(response.context["tasks"])) == 3

    def test_current_search_in_context(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("task-list") + "?q=myquery")
        assert response.context["current_search"] == "myquery"


@pytest.mark.django_db
class TestTaskExportView:
    def test_json_export_requires_login(self, client):
        response = client.get(reverse("task-export") + "?format=json")
        assert response.status_code == 302

    def test_json_export_contains_tasks(self, client):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user, title="My Task", status="todo")
        task.tags.add(tag)
        client.force_login(user)
        response = client.get(reverse("task-export") + "?format=json")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert data["meta"]["total_tasks"] == 1
        assert data["tasks"][0]["title"] == "My Task"
        assert tag.name in data["tasks"][0]["tags"]

    def test_csv_export_contains_header_row(self, client):
        user = UserFactory()
        TaskFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("task-export") + "?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response["Content-Type"]
        content = response.content.decode()
        assert "title" in content
        assert "status" in content

    def test_markdown_export_contains_checkboxes(self, client):
        user = UserFactory()
        TaskFactory(user=user, title="Undone Task", status="todo")
        TaskFactory(user=user, title="Done Task", status="done")
        client.force_login(user)
        response = client.get(reverse("task-export") + "?format=markdown")
        assert response.status_code == 200
        content = response.content.decode()
        assert "[ ]" in content
        assert "[x]" in content
        assert "Undone Task" in content
        assert "Done Task" in content

    def test_status_filter_applies_to_export(self, client):
        user = UserFactory()
        TaskFactory(user=user, status="todo")
        TaskFactory(user=user, status="done")
        client.force_login(user)
        response = client.get(reverse("task-export") + "?format=json&status=todo")
        data = json.loads(response.content)
        assert data["meta"]["total_tasks"] == 1
        assert data["tasks"][0]["status"] == "todo"

    def test_only_own_tasks_exported(self, client):
        user1 = UserFactory()
        user2 = UserFactory()
        TaskFactory(user=user1, title="User1 Task")
        TaskFactory(user=user2, title="User2 Task")
        client.force_login(user1)
        response = client.get(reverse("task-export") + "?format=json")
        data = json.loads(response.content)
        titles = [t["title"] for t in data["tasks"]]
        assert "User1 Task" in titles
        assert "User2 Task" not in titles

    def test_invalid_format_defaults_to_json(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("task-export") + "?format=bogus")
        assert response["Content-Type"] == "application/json"


@pytest.mark.django_db
def test_task_list_shows_large_dataset_notice_when_over_300_tasks(client):
    user = UserFactory()
    TaskFactory.create_batch(301, user=user)
    client.force_login(user)
    response = client.get(reverse("task-list"))
    assert response.status_code == 200
    assert response.context["show_large_dataset_notice"] is True


@pytest.mark.django_db
def test_task_list_no_large_dataset_notice_when_under_300_tasks(client):
    user = UserFactory()
    TaskFactory.create_batch(5, user=user)
    client.force_login(user)
    response = client.get(reverse("task-list"))
    assert response.context["show_large_dataset_notice"] is False


# --- Story 4.2: PWA and FAB tests ---


class TestManifestView:
    def test_manifest_returns_200(self, client):
        response = client.get("/manifest.json")
        assert response.status_code == 200

    def test_manifest_content_type(self, client):
        response = client.get("/manifest.json")
        assert "application/manifest+json" in response["Content-Type"]

    def test_manifest_has_required_fields(self, client):
        import json

        response = client.get("/manifest.json")
        data = json.loads(response.content)
        assert data["name"] == "Todo App"
        assert data["display"] == "standalone"
        assert "start_url" in data


class TestServiceWorkerView:
    def test_service_worker_returns_200(self, client):
        response = client.get("/service-worker.js")
        assert response.status_code == 200

    def test_service_worker_content_type(self, client):
        response = client.get("/service-worker.js")
        assert "javascript" in response["Content-Type"]

    def test_service_worker_allowed_header(self, client):
        response = client.get("/service-worker.js")
        assert response["Service-Worker-Allowed"] == "/"


@pytest.mark.django_db
def test_task_list_fab_present_for_authenticated_user(client):
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("task-list"))
    assert response.status_code == 200
    content = response.content.decode()
    # FAB links to task-create URL (/tasks/create/) and is hidden at md+ breakpoint
    assert reverse("task-create") in content
    assert "d-md-none" in content


# ---------------------------------------------------------------------------
# Story 4.5: Advanced Search & Discovery Features
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdvancedSearch:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_search_matches_description(self):
        user = UserFactory()
        task = TaskFactory(user=user, title="Unrelated", description="needle here")
        TaskFactory(user=user, title="Other", description="nothing")

        response = self._client(user).get(reverse("task-list") + "?q=needle")

        tasks = list(response.context["tasks"])
        assert task in tasks
        assert len(tasks) == 1

    def test_search_does_not_match_other_user_description(self):
        user = UserFactory()
        other = UserFactory()
        TaskFactory(user=other, title="Unrelated", description="needle here")

        response = self._client(user).get(reverse("task-list") + "?q=needle")

        assert list(response.context["tasks"]) == []

    def test_priority_filter_high(self):
        user = UserFactory()
        high_task = TaskFactory(user=user, priority="high")
        TaskFactory(user=user, priority="low")
        TaskFactory(user=user, priority="medium")

        response = self._client(user).get(reverse("task-list") + "?priority=high")

        tasks = list(response.context["tasks"])
        assert tasks == [high_task]

    def test_due_after_filter(self):
        user = UserFactory()
        future = date.today() + timedelta(days=5)
        past = date.today() - timedelta(days=5)
        future_task = TaskFactory(user=user, due_date=future)
        TaskFactory(user=user, due_date=past)

        cutoff = date.today().isoformat()
        response = self._client(user).get(reverse("task-list") + f"?due_after={cutoff}")

        tasks = list(response.context["tasks"])
        assert future_task in tasks
        assert all(t.due_date >= date.today() for t in tasks if t.due_date)

    def test_due_before_filter(self):
        user = UserFactory()
        past = date.today() - timedelta(days=5)
        future = date.today() + timedelta(days=5)
        past_task = TaskFactory(user=user, due_date=past)
        TaskFactory(user=user, due_date=future)

        cutoff = date.today().isoformat()
        response = self._client(user).get(
            reverse("task-list") + f"?due_before={cutoff}"
        )

        tasks = list(response.context["tasks"])
        assert past_task in tasks
        assert all(t.due_date <= date.today() for t in tasks if t.due_date)

    def test_result_count_in_context_when_filter_active(self):
        user = UserFactory()
        TaskFactory(user=user, title="matching task", description="")
        TaskFactory(user=user, title="other task", description="")

        response = self._client(user).get(reverse("task-list") + "?q=matching")

        assert response.context["any_filter_active"] is True
        assert response.context["result_count"] == 1


@pytest.mark.django_db
class TestTaskSearchSuggestView:
    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_search_suggest_returns_titles(self):
        user = UserFactory()
        TaskFactory(user=user, title="Fix the login bug")
        TaskFactory(user=user, title="Fix the logout bug")
        TaskFactory(user=user, title="Unrelated task")

        response = self._client(user).get(reverse("task-search-suggest") + "?q=fix")

        assert response.status_code == 200
        data = json.loads(response.content)
        titles = [item["title"] for item in data]
        assert "Fix the login bug" in titles
        assert "Fix the logout bug" in titles
        assert "Unrelated task" not in titles

    def test_search_suggest_requires_login(self, client):
        response = client.get(reverse("task-search-suggest") + "?q=foo")
        assert response.status_code == 302
        assert "login" in response.url

    def test_search_suggest_empty_q_returns_empty(self):
        user = UserFactory()
        TaskFactory(user=user, title="Some task")

        response = self._client(user).get(reverse("task-search-suggest") + "?q=")

        assert response.status_code == 200
        assert json.loads(response.content) == []


def test_highlight_filter():
    from apps.tasks.templatetags.task_tags import highlight

    result = str(highlight("Fix the login bug", "login"))
    assert "<mark>login</mark>" in result

    # Case-insensitive
    result_ci = str(highlight("Fix the LOGIN bug", "login"))
    assert "<mark>LOGIN</mark>" in result_ci

    # Empty query returns value unchanged
    result_empty = highlight("Fix the login bug", "")
    assert result_empty == "Fix the login bug"


# ---------------------------------------------------------------------------
# Health check endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHealthCheckEndpoints:
    def test_readiness_check_returns_200(self, client):
        response = client.get(reverse("health-ready"))
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check_returns_200(self, client):
        response = client.get(reverse("health-live"))
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


# ---------------------------------------------------------------------------
# Staff monitoring dashboard tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMonitoringDashboard:
    def test_monitoring_dashboard_redirects_anonymous(self, client):
        response = client.get(reverse("task-monitoring"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_monitoring_dashboard_redirects_non_staff(self):
        user = UserFactory(is_staff=False)
        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-monitoring"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_monitoring_dashboard_accessible_to_staff(self):
        user = UserFactory(is_staff=True)
        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-monitoring"))
        assert response.status_code == 200

    def test_monitoring_dashboard_context_has_stats(self):
        user = UserFactory(is_staff=True)
        client = Client()
        client.force_login(user)
        response = client.get(reverse("task-monitoring"))
        assert response.status_code == 200
        ctx = response.context
        assert "total_users" in ctx
        assert "active_users_today" in ctx
        assert "total_tasks" in ctx
        assert "tasks_created_today" in ctx
        assert "total_tags" in ctx


# ---------------------------------------------------------------------------
# Failed login signal handler test
# ---------------------------------------------------------------------------


def test_failed_login_signal_handler_logs_warning(caplog):
    import logging

    from django.test import RequestFactory

    from apps.accounts.signals import log_failed_login

    factory = RequestFactory()
    request = factory.post("/accounts/login/")
    request.META["REMOTE_ADDR"] = "127.0.0.1"

    with caplog.at_level(logging.WARNING, logger="apps.accounts"):
        log_failed_login(
            sender=None,
            credentials={"username": "testuser"},
            request=request,
        )

    assert any(
        "Failed login attempt for username: testuser" in r.message
        for r in caplog.records
    )
