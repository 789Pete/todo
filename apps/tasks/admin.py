from django.contrib import admin

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
    list_display = ("name", "user", "color", "created_at")
    list_filter = ("color", "user")
    search_fields = ("name",)
