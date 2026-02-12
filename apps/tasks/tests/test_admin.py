import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.tasks.admin import TagAdmin, TaskAdmin
from apps.tasks.models import Tag, Task

from .factories import TagFactory, TaskFactory


@pytest.mark.django_db
class TestTaskAdmin:
    def test_task_registered_in_admin(self):
        assert TaskAdmin is not None
        admin_instance = TaskAdmin(Task, AdminSite())
        assert admin_instance is not None

    def test_admin_task_list_page_loads(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        url = reverse("admin:tasks_task_changelist")
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_task_list_with_data(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        TaskFactory(user=user)
        client.force_login(user)
        url = reverse("admin:tasks_task_changelist")
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestTagAdmin:
    def test_tag_registered_in_admin(self):
        assert TagAdmin is not None
        admin_instance = TagAdmin(Tag, AdminSite())
        assert admin_instance is not None

    def test_admin_tag_list_page_loads(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(user)
        url = reverse("admin:tasks_tag_changelist")
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_tag_list_with_data(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        TagFactory(user=user)
        client.force_login(user)
        url = reverse("admin:tasks_tag_changelist")
        response = client.get(url)
        assert response.status_code == 200
