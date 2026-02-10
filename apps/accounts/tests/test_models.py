import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_has_uuid_primary_key(self):
        user = UserFactory()
        assert isinstance(user.pk, uuid.UUID)

    def test_user_creation_with_required_fields(self):
        user = UserFactory(username="testuser", email="test@example.com")
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_str_returns_username(self):
        user = UserFactory(username="alice")
        assert str(user) == "alice"

    def test_email_must_be_unique(self):
        UserFactory(email="duplicate@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="duplicate@example.com")

    def test_user_table_name(self):
        assert User._meta.db_table == "users"
