import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestGraphView:
    def test_graph_view_requires_authentication(self, client):
        url = reverse("graph-view")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_graph_view_returns_200_for_authenticated_user(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("graph-view")
        response = client.get(url)
        assert response.status_code == 200

    def test_graph_view_uses_correct_template(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("graph-view")
        response = client.get(url)
        assert "visualization/graph.html" in [t.name for t in response.templates]

    def test_graph_view_contains_graph_container(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("graph-view")
        response = client.get(url)
        assert b'id="network-graph"' in response.content
