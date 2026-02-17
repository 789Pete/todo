import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Tag(models.Model):
    """Tag model for categorizing tasks. Owned by a user, reusable across their tasks."""

    COLOR_CHOICES = [
        ("#FF6B6B", "Red"),
        ("#4ECDC4", "Teal"),
        ("#45B7D1", "Blue"),
        ("#FFA07A", "Orange"),
        ("#98D8C8", "Mint"),
        ("#F7DC6F", "Yellow"),
        ("#BB8FCE", "Purple"),
        ("#85C1E2", "Sky Blue"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        choices=COLOR_CHOICES,
        default="#4ECDC4",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        unique_together = [["user", "name"]]
        indexes = [
            models.Index(fields=["user", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.color})"

    def clean(self):
        """Validate tag name uniqueness (case-insensitive) and color format."""
        # Case-insensitive uniqueness check
        if self.name and self.user_id:
            duplicate = (
                Tag.objects.filter(user=self.user, name__iexact=self.name)
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicate:
                raise ValidationError(
                    {"name": f"Tag '{self.name}' already exists (case-insensitive)."}
                )

        # Hex color code validation
        if self.color and not re.match(r"^#[0-9A-Fa-f]{6}$", self.color):
            raise ValidationError(
                {"color": "Color must be a valid hex code (e.g., #FF6B6B)."}
            )

    @property
    def task_count(self):
        """Return number of tasks with this tag."""
        return self.tasks.count()

    def get_related_tags(self):
        """Get tags that frequently co-occur with this tag on tasks."""
        from django.db.models import Count

        return (
            Tag.objects.filter(tasks__tags=self)
            .exclude(id=self.id)
            .annotate(shared_count=Count("tasks"))
            .order_by("-shared_count")[:5]
        )


class Task(models.Model):
    """Task model representing a single to-do item. Belongs to a user and can have multiple tags."""

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="todo",
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
        db_index=True,
    )
    due_date = models.DateField(null=True, blank=True)
    position = models.IntegerField(default=0, help_text="For manual ordering")
    tags = models.ManyToManyField("Tag", related_name="tasks", blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["position", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "priority"]),
            models.Index(fields=["user", "due_date"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        return (
            self.due_date
            and self.due_date < timezone.now().date()
            and self.status != "done"
        )

    @property
    def days_until_due(self):
        """Calculate days until due date."""
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days

    def mark_complete(self):
        """Mark task as done and record completion timestamp."""
        if self.status != "done":
            self.status = "done"
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at", "updated_at"])

    def mark_incomplete(self):
        """Mark task as not done and clear completion timestamp."""
        self.status = "todo"
        self.completed_at = None
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def get_related_tasks(self):
        """Get tasks sharing tags with this task, excluding self."""
        return (
            Task.objects.filter(user=self.user, tags__in=self.tags.all())
            .exclude(id=self.id)
            .distinct()
        )
