from django.urls import path

from apps.tasks.views import (
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskUpdateView,
)

urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
    path("create/", TaskCreateView.as_view(), name="task-create"),
    path("<uuid:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("<uuid:pk>/edit/", TaskUpdateView.as_view(), name="task-update"),
    path("<uuid:pk>/delete/", TaskDeleteView.as_view(), name="task-delete"),
]
