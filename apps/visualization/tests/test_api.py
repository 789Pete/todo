import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.tasks.tests.factories import TagFactory, TaskFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestGraphDataAPI:
    def test_requires_authentication(self, api_client):
        # DRF with SessionAuthentication returns 403 (not 401) for anonymous requests
        # because no WWW-Authenticate header is set. Either way, unauthenticated → denied.
        url = reverse("api-graph-data")
        response = api_client.get(url)
        assert response.status_code in (401, 403)

    def test_returns_200_for_authenticated_user(self, authenticated_client):
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_response_has_required_keys(self, authenticated_client):
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "stats" in data

    def test_stats_has_required_keys(self, authenticated_client):
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        stats = response.json()["stats"]
        assert "total_tasks" in stats
        assert "total_tags" in stats
        assert "filtered_tasks" in stats
        assert "filtered_tags" in stats

    def test_returns_only_user_data(self, api_client):
        user1 = UserFactory()
        user2 = UserFactory()
        TaskFactory(user=user1, title="User1 Task")
        api_client.force_authenticate(user=user2)
        url = reverse("api-graph-data")
        response = api_client.get(url)
        data = response.json()
        assert data["stats"]["total_tasks"] == 0
        assert data["nodes"] == []

    def test_returns_user_tasks(self, authenticated_client, user):
        TaskFactory(user=user)
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        data = response.json()
        assert data["stats"]["total_tasks"] == 1
        assert len([n for n in data["nodes"] if n["group"] != "tag"]) == 1

    def test_filter_status_param(self, authenticated_client, user):
        TaskFactory(user=user, status="todo")
        TaskFactory(user=user, status="done")
        url = reverse("api-graph-data")
        response = authenticated_client.get(url, {"filter_status": "done"})
        data = response.json()
        assert data["stats"]["filtered_tasks"] == 1
        assert data["stats"]["total_tasks"] == 2
        task_nodes = [n for n in data["nodes"] if n["group"] != "tag"]
        assert task_nodes[0]["group"] == "done"

    def test_filter_tag_param(self, authenticated_client, user):
        work_tag = TagFactory(user=user, name="Work")
        personal_tag = TagFactory(user=user, name="Personal")
        TaskFactory(user=user, tags=[work_tag])
        TaskFactory(user=user, tags=[personal_tag])
        url = reverse("api-graph-data")
        response = authenticated_client.get(url, {"filter_tag": "Work"})
        data = response.json()
        assert data["stats"]["filtered_tasks"] == 1

    def test_empty_graph_for_user_with_no_tasks(self, authenticated_client):
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        data = response.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["stats"]["total_tasks"] == 0
        assert data["stats"]["total_tags"] == 0

    def test_task_and_tag_nodes_in_response(self, authenticated_client, user):
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        data = response.json()
        task_nodes = [n for n in data["nodes"] if n["group"] != "tag"]
        tag_nodes = [n for n in data["nodes"] if n["group"] == "tag"]
        assert len(task_nodes) == 1
        assert len(tag_nodes) == 1
        assert len(data["edges"]) == 1

    def test_returns_json_content_type(self, authenticated_client):
        url = reverse("api-graph-data")
        response = authenticated_client.get(url)
        assert "application/json" in response["Content-Type"]
