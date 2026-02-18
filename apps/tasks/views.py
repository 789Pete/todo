import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, IntegerField, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.tasks.forms import TagForm, TaskForm
from apps.tasks.models import Tag, Task

SORT_OPTIONS = {
    "priority": "priority",
    "-priority": "-priority",
    "due_date": "due_date",
    "-due_date": "-due_date",
    "created_at": "created_at",
    "-created_at": "-created_at",
}

PRIORITY_ORDER = Case(
    When(priority="high", then=0),
    When(priority="medium", then=1),
    When(priority="low", then=2),
    output_field=IntegerField(),
)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25

    def get_queryset(self):
        qs = Task.objects.filter(user=self.request.user).prefetch_related("tags")
        status = self.request.GET.get("status")
        if status == "active":
            qs = qs.filter(status__in=["todo", "in_progress"])
        elif status in ("todo", "in_progress", "done"):
            qs = qs.filter(status=status)
        sort = self.request.GET.get("sort")
        if sort in SORT_OPTIONS:
            qs = qs.order_by(SORT_OPTIONS[sort])
        else:
            qs = qs.order_by(PRIORITY_ORDER, "-created_at")
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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


class TaskToggleStatusView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        task = get_object_or_404(Task.objects.filter(user=request.user), pk=pk)
        if task.status != "done":
            task.mark_complete()
            messages.success(request, f'Task "{task.title}" marked as complete!')
        else:
            task.mark_incomplete()
            messages.success(request, f'Task "{task.title}" marked as incomplete.')
        return redirect("task-list")


# --- Tag Views ---


class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = "tasks/tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return (
            Tag.objects.filter(user=self.request.user)
            .annotate(num_tasks=Count("tasks"))
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["color_choices"] = Tag.COLOR_CHOICES
        return context


class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = "tasks/tag_form.html"
    success_url = reverse_lazy("tag-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            form.instance.full_clean()
        except Exception as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field if field != "__all__" else None, error)
            return self.form_invalid(form)
        response = super().form_valid(form)
        messages.success(
            self.request, f'Tag "{self.object.name}" created successfully!'
        )
        return response


class TagUpdateView(LoginRequiredMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = "tasks/tag_form.html"
    success_url = reverse_lazy("tag-list")

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            form.instance.full_clean()
        except Exception as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field if field != "__all__" else None, error)
            return self.form_invalid(form)
        response = super().form_valid(form)
        messages.success(
            self.request, f'Tag "{self.object.name}" updated successfully!'
        )
        return response


class TagDeleteView(LoginRequiredMixin, DeleteView):
    model = Tag
    template_name = "tasks/tag_confirm_delete.html"
    success_url = reverse_lazy("tag-list")

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_count"] = self.object.tasks.count()
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f'Tag "{self.object.name}" deleted successfully.'
        )
        return super().form_valid(form)


class TagQuickCreateView(LoginRequiredMixin, View):
    """AJAX endpoint to create a tag on-the-fly from the task form."""

    http_method_names = ["post"]

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        name = data.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Tag name cannot be empty."}, status=400)

        # Auto-assign color: pick least-used color among user's tags
        user_tag_colors = list(
            Tag.objects.filter(user=request.user).values_list("color", flat=True)
        )
        color = _pick_auto_color(user_tag_colors)

        tag = Tag(user=request.user, name=name, color=color)
        try:
            tag.full_clean()
        except Exception as e:
            errors = e.message_dict
            error_msg = next(iter(next(iter(errors.values()))), "Validation error.")
            return JsonResponse({"error": error_msg}, status=400)

        tag.save()
        return JsonResponse(
            {"id": str(tag.pk), "name": tag.name, "color": tag.color}, status=201
        )


class TagAutocompleteView(LoginRequiredMixin, View):
    """AJAX endpoint for tag autocomplete suggestions."""

    http_method_names = ["get"]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        tags = Tag.objects.filter(user=request.user)
        if q:
            tags = tags.filter(name__icontains=q)
        tags = tags[:10]
        return JsonResponse(
            [{"id": str(t.pk), "name": t.name, "color": t.color} for t in tags],
            safe=False,
        )


class TagBulkEditView(LoginRequiredMixin, View):
    """Handle bulk tag operations: delete or change color."""

    http_method_names = ["post"]

    def post(self, request):
        tag_ids = request.POST.getlist("tag_ids")
        action = request.POST.get("bulk_action", "")

        if not tag_ids:
            messages.warning(request, "No tags selected.")
            return redirect("tag-list")

        user_tags = Tag.objects.filter(user=request.user, pk__in=tag_ids)
        count = user_tags.count()

        if not count:
            messages.warning(request, "No valid tags found.")
            return redirect("tag-list")

        if action == "delete":
            user_tags.delete()
            messages.success(request, f"Deleted {count} tag(s).")
        elif action.startswith("color:"):
            new_color = action.split(":", 1)[1]
            valid_colors = [c[0] for c in Tag.COLOR_CHOICES]
            if new_color in valid_colors:
                user_tags.update(color=new_color)
                messages.success(request, f"Updated color for {count} tag(s).")
            else:
                messages.error(request, "Invalid color selected.")
        else:
            messages.warning(request, "No action selected.")

        return redirect("tag-list")


def _pick_auto_color(existing_colors):
    """Pick the least-used color from COLOR_CHOICES."""
    color_counts = {}
    for hex_code, _label in Tag.COLOR_CHOICES:
        color_counts[hex_code] = 0
    for c in existing_colors:
        if c in color_counts:
            color_counts[c] += 1
    return min(color_counts, key=color_counts.get)
