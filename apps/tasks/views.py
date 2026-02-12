from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.tasks.forms import TaskForm
from apps.tasks.models import Task

SORT_OPTIONS = {
    "priority": "priority",
    "-priority": "-priority",
    "due_date": "due_date",
    "-due_date": "-due_date",
    "created_at": "created_at",
    "-created_at": "-created_at",
}


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25

    def get_queryset(self):
        qs = Task.objects.filter(user=self.request.user).prefetch_related("tags")
        status = self.request.GET.get("status")
        if status in ("todo", "in_progress", "done"):
            qs = qs.filter(status=status)
        sort = self.request.GET.get("sort")
        if sort in SORT_OPTIONS:
            qs = qs.order_by(SORT_OPTIONS[sort])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "")
        context["current_sort"] = self.request.GET.get("sort", "")
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).prefetch_related("tags")


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, f'Task "{self.object.title}" created successfully!'
        )
        return response

    def get_success_url(self):
        return reverse("task-detail", kwargs={"pk": self.object.pk})


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Task "{self.object.title}" updated successfully!'
        )
        return response

    def get_success_url(self):
        return reverse("task-detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task-list")

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(
            self.request, f'Task "{self.object.title}" deleted successfully.'
        )
        return super().form_valid(form)
