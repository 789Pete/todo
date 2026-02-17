from django.contrib import admin
from django.db.models import Count

from .models import Tag, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "title",
        "user",
        "status",
        "priority",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "priority", "due_date", "created_at")
    search_fields = ("title", "description")
    list_editable = ("status", "priority")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color", "tag_task_count", "created_at")
    list_filter = ("color", "user")
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_tasks=Count("tasks"))

    @admin.display(description="Tasks", ordering="num_tasks")
    def tag_task_count(self, obj):
        return obj.num_tasks
