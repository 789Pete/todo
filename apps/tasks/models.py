import uuid

from django.conf import settings
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
