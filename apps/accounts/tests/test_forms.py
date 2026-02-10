import pytest

from apps.accounts.forms import ProfileUpdateForm, UserRegistrationForm

from .factories import UserFactory


@pytest.mark.django_db
class TestUserRegistrationForm:
    def test_valid_registration(self):
        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password1": "securepass123!!",
                "password2": "securepass123!!",
            }
        )
        assert form.is_valid()

    def test_duplicate_email_rejected(self):
        UserFactory(email="taken@example.com")
        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "taken@example.com",
                "password1": "securepass123!!",
                "password2": "securepass123!!",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_weak_password_rejected(self):
        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password1": "short",
                "password2": "short",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_mismatched_passwords_rejected(self):
        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "new@example.com",
                "password1": "securepass123!!",
                "password2": "differentpass123!!",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors


@pytest.mark.django_db
class TestProfileUpdateForm:
    def test_valid_profile_update(self):
        user = UserFactory()
        form = ProfileUpdateForm(
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": user.email,
            },
            instance=user,
        )
        assert form.is_valid()

    def test_duplicate_email_rejected(self):
        user1 = UserFactory(email="user1@example.com")
        UserFactory(email="user2@example.com")
        form = ProfileUpdateForm(
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "user2@example.com",
            },
            instance=user1,
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_keeping_own_email_is_valid(self):
        user = UserFactory(email="mine@example.com")
        form = ProfileUpdateForm(
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "mine@example.com",
            },
            instance=user,
        )
        assert form.is_valid()
