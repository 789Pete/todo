from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.tasks.models import Task
from apps.tasks.tests.factories import TaskFactory


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
