from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.accounts.tests.factories import UserFactory
from apps.tasks.models import Tag, Task

from .factories import TagFactory, TaskFactory


@pytest.mark.django_db
class TestTaskModel:
    def test_task_creation_with_all_fields(self):
        user = UserFactory()
        task = TaskFactory(
            user=user,
            title="Test Task",
            description="A description",
            status="in_progress",
            priority="high",
            due_date=date.today() + timedelta(days=3),
            position=5,
        )
        assert task.title == "Test Task"
        assert task.description == "A description"
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.due_date == date.today() + timedelta(days=3)
        assert task.position == 5
        assert task.user == user
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_has_uuid_primary_key(self):
        task = TaskFactory()
        assert task.id is not None
        assert len(str(task.id)) == 36  # UUID format

    def test_task_belongs_to_user(self):
        user = UserFactory()
        task = TaskFactory(user=user)
        assert task.user == user
        assert task in user.tasks.all()

    def test_task_str_representation(self):
        task = TaskFactory(title="My Task", status="in_progress")
        assert str(task) == "My Task (In Progress)"

    def test_task_str_with_todo_status(self):
        task = TaskFactory(title="Todo Item", status="todo")
        assert str(task) == "Todo Item (To Do)"

    def test_task_str_with_done_status(self):
        task = TaskFactory(title="Done Task", status="done")
        assert str(task) == "Done Task (Done)"

    def test_default_status_is_todo(self):
        task = TaskFactory()
        assert task.status == "todo"

    def test_default_priority_is_medium(self):
        task = TaskFactory()
        assert task.priority == "medium"

    def test_is_overdue_when_due_date_past_and_not_done(self):
        task = TaskFactory(
            due_date=date.today() - timedelta(days=1),
            status="todo",
        )
        assert task.is_overdue is True

    def test_is_overdue_false_when_status_is_done(self):
        task = TaskFactory(
            due_date=date.today() - timedelta(days=1),
            status="done",
        )
        assert task.is_overdue is False

    def test_is_overdue_false_when_due_date_in_future(self):
        task = TaskFactory(
            due_date=date.today() + timedelta(days=1),
            status="todo",
        )
        assert task.is_overdue is False

    def test_is_overdue_false_when_due_date_is_none(self):
        task = TaskFactory(due_date=None)
        assert not task.is_overdue

    def test_is_overdue_with_in_progress_status(self):
        task = TaskFactory(
            due_date=date.today() - timedelta(days=1),
            status="in_progress",
        )
        assert task.is_overdue is True

    def test_days_until_due_positive(self):
        task = TaskFactory(due_date=date.today() + timedelta(days=5))
        assert task.days_until_due == 5

    def test_days_until_due_negative(self):
        task = TaskFactory(due_date=date.today() - timedelta(days=3))
        assert task.days_until_due == -3

    def test_days_until_due_none_when_no_due_date(self):
        task = TaskFactory(due_date=None)
        assert task.days_until_due is None

    def test_invalid_status_fails_validation(self):
        task = TaskFactory.build(status="invalid")
        with pytest.raises(ValidationError):
            task.full_clean()

    def test_invalid_priority_fails_validation(self):
        task = TaskFactory.build(priority="invalid")
        with pytest.raises(ValidationError):
            task.full_clean()

    def test_blank_title_fails_validation(self):
        task = TaskFactory.build(title="")
        with pytest.raises(ValidationError):
            task.full_clean()

    def test_due_date_is_optional(self):
        task = TaskFactory(due_date=None)
        task.full_clean()  # Should not raise

    def test_task_tag_many_to_many(self):
        user = UserFactory()
        task = TaskFactory(user=user)
        tag1 = TagFactory(user=user, name="Work")
        tag2 = TagFactory(user=user, name="Personal")
        task.tags.add(tag1, tag2)
        assert task.tags.count() == 2
        assert tag1 in task.tags.all()
        assert tag2 in task.tags.all()

    def test_tag_references_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        assert task in tag.tasks.all()

    def test_cascade_delete_user_deletes_tasks(self):
        user = UserFactory()
        TaskFactory(user=user)
        TaskFactory(user=user)
        assert Task.objects.filter(user=user).count() == 2
        user.delete()
        assert Task.objects.filter(user=user).count() == 0

    def test_task_table_name(self):
        assert Task._meta.db_table == "tasks"


@pytest.mark.django_db
class TestTagModel:
    def test_tag_creation(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Work", color="#FF6B6B")
        assert tag.name == "Work"
        assert tag.color == "#FF6B6B"
        assert tag.user == user
        assert tag.created_at is not None

    def test_tag_has_uuid_primary_key(self):
        tag = TagFactory()
        assert tag.id is not None
        assert len(str(tag.id)) == 36

    def test_tag_str_representation(self):
        tag = TagFactory(name="Urgent", color="#FF6B6B")
        assert str(tag) == "Urgent (#FF6B6B)"

    def test_tag_name_unique_per_user(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")
        with pytest.raises(IntegrityError):
            TagFactory(user=user, name="Work")

    def test_tag_name_can_duplicate_across_users(self):
        user1 = UserFactory()
        user2 = UserFactory()
        tag1 = TagFactory(user=user1, name="Work")
        tag2 = TagFactory(user=user2, name="Work")
        assert tag1.name == tag2.name
        assert tag1.user != tag2.user

    def test_cascade_delete_user_deletes_tags(self):
        user = UserFactory()
        TagFactory(user=user)
        TagFactory(user=user, name="Other")
        assert Tag.objects.filter(user=user).count() == 2
        user.delete()
        assert Tag.objects.filter(user=user).count() == 0

    def test_tag_table_name(self):
        assert Tag._meta.db_table == "tags"

    def test_default_color(self):
        tag = TagFactory()
        assert tag.color == "#4ECDC4"
