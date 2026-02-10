import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestRegisterView:
    def test_register_page_renders(self, client):
        response = client.get(reverse("register"))
        assert response.status_code == 200
        assert b"Create Account" in response.content

    def test_successful_registration(self, client):
        response = client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "securepass123!!",
                "password2": "securepass123!!",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("home")
        assert User.objects.filter(username="newuser").exists()

    def test_registration_auto_logs_in(self, client):
        client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "securepass123!!",
                "password2": "securepass123!!",
            },
        )
        response = client.get(reverse("home"))
        assert response.wsgi_request.user.is_authenticated

    def test_registration_with_invalid_data_shows_form(self, client):
        response = client.post(
            reverse("register"),
            {
                "username": "",
                "email": "bad",
                "password1": "short",
                "password2": "short",
            },
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_renders(self, client):
        response = client.get(reverse("login"))
        assert response.status_code == 200
        assert b"Log In" in response.content

    def test_successful_login(self, client):
        UserFactory(username="testuser")
        response = client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123!!"},
        )
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_invalid_login(self, client):
        response = client.post(
            reverse("login"),
            {"username": "nonexistent", "password": "wrongpass123!!"},
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.content


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_redirects_to_login(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("logout"))
        assert response.status_code == 302
        assert reverse("login") in response.url


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_authentication(self, client):
        response = client.get(reverse("profile"))
        assert response.status_code == 302
        assert reverse("login") in response.url

    def test_profile_page_renders_for_authenticated_user(self, client):
        user = UserFactory(username="alice")
        client.force_login(user)
        response = client.get(reverse("profile"))
        assert response.status_code == 200
        assert b"alice" in response.content

    def test_profile_update(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse("profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": user.email,
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_unauthenticated_redirect_includes_next(self, client):
        response = client.get(reverse("profile"))
        assert response.status_code == 302
        assert f"?next={reverse('profile')}" in response.url


@pytest.mark.django_db
class TestPasswordResetView:
    def test_password_reset_page_renders(self, client):
        response = client.get(reverse("password-reset"))
        assert response.status_code == 200
        assert b"Reset Password" in response.content

    def test_password_reset_sends_email(self, client, mailoutbox):
        UserFactory(email="test@example.com")
        response = client.post(
            reverse("password-reset"),
            {"email": "test@example.com"},
        )
        assert response.status_code == 302
        assert len(mailoutbox) == 1

    def test_password_reset_done_page_renders(self, client):
        response = client.get(reverse("password-reset-done"))
        assert response.status_code == 200
        assert b"Check Your Email" in response.content

    def test_password_reset_complete_page_renders(self, client):
        response = client.get(reverse("password-reset-complete"))
        assert response.status_code == 200
        assert b"Password Reset Complete" in response.content
