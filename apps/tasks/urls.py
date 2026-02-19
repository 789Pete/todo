from django.urls import path

from apps.tasks.views import (
    TagAutocompleteView,
    TagBulkEditView,
    TagColorUpdateView,
    TagCreateView,
    TagDeleteView,
    TagExportView,
    TagListView,
    TagMergeView,
    TagNameUpdateView,
    TagQuickCreateView,
    TagUpdateView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskToggleStatusView,
    TaskUpdateView,
)

urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
    path("create/", TaskCreateView.as_view(), name="task-create"),
    path("<uuid:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("<uuid:pk>/edit/", TaskUpdateView.as_view(), name="task-update"),
    path("<uuid:pk>/delete/", TaskDeleteView.as_view(), name="task-delete"),
    path(
        "<uuid:pk>/toggle/", TaskToggleStatusView.as_view(), name="task-toggle-status"
    ),
    # Tag URLs
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("tags/create/", TagCreateView.as_view(), name="tag-create"),
    path("tags/<uuid:pk>/edit/", TagUpdateView.as_view(), name="tag-update"),
    path("tags/<uuid:pk>/delete/", TagDeleteView.as_view(), name="tag-delete"),
    path("tags/quick-create/", TagQuickCreateView.as_view(), name="tag-quick-create"),
    path("tags/autocomplete/", TagAutocompleteView.as_view(), name="tag-autocomplete"),
    path("tags/bulk-edit/", TagBulkEditView.as_view(), name="tag-bulk-edit"),
    path("tags/export/", TagExportView.as_view(), name="tag-export"),
    path(
        "tags/<uuid:pk>/color/", TagColorUpdateView.as_view(), name="tag-color-update"
    ),
    path("tags/<uuid:pk>/name/", TagNameUpdateView.as_view(), name="tag-name-update"),
    path("tags/<uuid:pk>/merge/", TagMergeView.as_view(), name="tag-merge"),
]
