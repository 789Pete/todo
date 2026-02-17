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

    def test_mark_complete_sets_status_and_completed_at(self):
        task = TaskFactory(status="todo")
        task.mark_complete()
        task.refresh_from_db()
        assert task.status == "done"
        assert task.completed_at is not None

    def test_mark_incomplete_sets_todo_and_clears_completed_at(self):
        task = TaskFactory(status="done")
        task.mark_complete()  # ensure completed_at is set
        task.mark_incomplete()
        task.refresh_from_db()
        assert task.status == "todo"
        assert task.completed_at is None

    def test_completed_at_is_none_for_new_tasks(self):
        task = TaskFactory(status="todo")
        assert task.completed_at is None

    def test_mark_complete_on_already_done_task_is_noop(self):
        task = TaskFactory(status="todo")
        task.mark_complete()
        task.refresh_from_db()
        first_completed_at = task.completed_at
        task.mark_complete()  # should not change
        task.refresh_from_db()
        assert task.completed_at == first_completed_at

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

    # --- Case-insensitive uniqueness (clean method) ---

    def test_clean_rejects_case_insensitive_duplicate(self):
        user = UserFactory()
        TagFactory(user=user, name="Work")
        tag = Tag(user=user, name="work", color="#4ECDC4")
        with pytest.raises(ValidationError, match="already exists"):
            tag.clean()

    def test_clean_allows_same_name_different_user(self):
        user1 = UserFactory()
        user2 = UserFactory()
        TagFactory(user=user1, name="Work")
        tag = Tag(user=user2, name="Work", color="#4ECDC4")
        tag.clean()  # Should not raise

    def test_clean_allows_editing_own_tag(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Work")
        tag.name = "Work"  # Same name, same tag
        tag.clean()  # Should not raise

    # --- Hex color validation ---

    def test_clean_rejects_invalid_color_word(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="red")
        with pytest.raises(ValidationError, match="valid hex code"):
            tag.clean()

    def test_clean_rejects_invalid_hex_chars(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="#GGGGGG")
        with pytest.raises(ValidationError, match="valid hex code"):
            tag.clean()

    def test_clean_rejects_short_hex(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="#FFF")
        with pytest.raises(ValidationError, match="valid hex code"):
            tag.clean()

    def test_clean_rejects_hex_without_hash(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="FF6B6B")
        with pytest.raises(ValidationError, match="valid hex code"):
            tag.clean()

    def test_clean_accepts_valid_hex_color(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="#FF6B6B")
        tag.clean()  # Should not raise

    def test_clean_accepts_lowercase_hex(self):
        user = UserFactory()
        tag = Tag(user=user, name="Test", color="#ff6b6b")
        tag.clean()  # Should not raise

    # --- task_count property ---

    def test_task_count_zero(self):
        tag = TagFactory()
        assert tag.task_count == 0

    def test_task_count_with_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        task1.tags.add(tag)
        task2.tags.add(tag)
        assert tag.task_count == 2

    def test_task_count_only_counts_own_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        # Another user's task with a different tag shouldn't affect count
        assert tag.task_count == 1

    # --- get_related_tags ---

    def test_get_related_tags_returns_co_occurring_tags(self):
        user = UserFactory()
        tag_a = TagFactory(user=user, name="A")
        tag_b = TagFactory(user=user, name="B")
        tag_c = TagFactory(user=user, name="C")
        task = TaskFactory(user=user)
        task.tags.add(tag_a, tag_b, tag_c)
        related = tag_a.get_related_tags()
        assert tag_b in related
        assert tag_c in related

    def test_get_related_tags_excludes_self(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Solo")
        task = TaskFactory(user=user)
        task.tags.add(tag)
        related = tag.get_related_tags()
        assert tag not in related

    def test_get_related_tags_empty_when_no_shared_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Lonely")
        assert list(tag.get_related_tags()) == []

    def test_get_related_tags_ordered_by_frequency(self):
        user = UserFactory()
        tag_main = TagFactory(user=user, name="Main")
        tag_freq = TagFactory(user=user, name="Frequent")
        tag_rare = TagFactory(user=user, name="Rare")
        # tag_freq co-occurs on 2 tasks, tag_rare on 1
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        task1.tags.add(tag_main, tag_freq)
        task2.tags.add(tag_main, tag_freq, tag_rare)
        related = list(tag_main.get_related_tags())
        assert related[0] == tag_freq
        assert related[1] == tag_rare

    # --- Cascade deletion: tag deletion ---

    def test_deleting_tag_does_not_delete_tasks(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        tag_id = tag.id
        task_id = task.id
        tag.delete()
        assert Task.objects.filter(id=task_id).exists()
        assert not Tag.objects.filter(id=tag_id).exists()
        task.refresh_from_db()
        assert task.tags.count() == 0

    def test_deleting_task_does_not_delete_tags(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        tag_id = tag.id
        task.delete()
        assert Tag.objects.filter(id=tag_id).exists()

    def test_m2m_through_table_cleaned_on_tag_delete(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        assert task.tags.count() == 1
        tag.delete()
        task.refresh_from_db()
        assert task.tags.count() == 0

    def test_m2m_through_table_cleaned_on_task_delete(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        assert tag.tasks.count() == 1
        task.delete()
        assert tag.tasks.count() == 0

    # --- M2M through table functionality ---

    def test_m2m_add_remove_tags(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        assert tag in task.tags.all()
        task.tags.remove(tag)
        assert tag not in task.tags.all()

    def test_m2m_query_from_tag_side(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        task1.tags.add(tag)
        task2.tags.add(tag)
        assert set(tag.tasks.all()) == {task1, task2}


@pytest.mark.django_db
class TestTaskRelatedTasks:
    def test_get_related_tasks_returns_tasks_sharing_tags(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        task1.tags.add(tag)
        task2.tags.add(tag)
        related = task1.get_related_tasks()
        assert task2 in related
        assert task1 not in related

    def test_get_related_tasks_excludes_self(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)
        assert task not in task.get_related_tasks()

    def test_get_related_tasks_empty_when_no_tags(self):
        task = TaskFactory()
        assert list(task.get_related_tasks()) == []

    def test_get_related_tasks_distinct(self):
        user = UserFactory()
        tag1 = TagFactory(user=user, name="A")
        tag2 = TagFactory(user=user, name="B")
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        # task2 shares both tags with task1 — should appear only once
        task1.tags.add(tag1, tag2)
        task2.tags.add(tag1, tag2)
        related = list(task1.get_related_tasks())
        assert len(related) == 1
        assert related[0] == task2

    def test_get_related_tasks_only_same_user(self):
        user1 = UserFactory()
        user2 = UserFactory()
        tag = TagFactory(user=user1)
        task1 = TaskFactory(user=user1)
        task2 = TaskFactory(user=user2)
        task1.tags.add(tag)
        task2.tags.add(tag)
        # task2 belongs to different user, should not appear
        assert task2 not in task1.get_related_tasks()
