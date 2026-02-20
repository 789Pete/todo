import csv
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, IntegerField, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
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


def _build_tag_add_url(request, tag_pk):
    """Return URL with tag_pk added to the 'tags' filter param."""
    params = request.GET.copy()
    existing = params.getlist("tags")
    if str(tag_pk) not in existing:
        existing.append(str(tag_pk))
    params.setlist("tags", existing)
    params.pop("page", None)
    return "?" + params.urlencode()


def _build_tag_remove_url(request, tag_pk):
    """Return URL with tag_pk removed from the 'tags' filter param."""
    params = request.GET.copy()
    existing = [t for t in params.getlist("tags") if t != str(tag_pk)]
    params.setlist("tags", existing)
    params.pop("page", None)
    return "?" + params.urlencode()


def _build_clear_tags_url(request):
    """Return URL with all tag filter params removed."""
    params = request.GET.copy()
    params.pop("tags", None)
    params.pop("tag_mode", None)
    params.pop("page", None)
    return "?" + params.urlencode() if params else "?"


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
        tag_ids = self.request.GET.getlist("tags")
        if tag_ids:
            tag_mode = self.request.GET.get("tag_mode", "and")
            if tag_mode == "or":
                qs = qs.filter(tags__pk__in=tag_ids).distinct()
            else:
                for tag_id in tag_ids:
                    qs = qs.filter(tags__pk=tag_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "")
        context["current_sort"] = self.request.GET.get("sort", "")

        tag_ids = self.request.GET.getlist("tags")
        tag_mode = self.request.GET.get("tag_mode", "and")

        active_tags = (
            Tag.objects.filter(user=self.request.user, pk__in=tag_ids)
            if tag_ids
            else Tag.objects.none()
        )
        all_user_tags = Tag.objects.filter(user=self.request.user)

        tag_add_urls = {
            str(tag.pk): _build_tag_add_url(self.request, tag.pk)
            for tag in all_user_tags
        }
        tag_remove_urls = {
            str(tag.pk): _build_tag_remove_url(self.request, tag.pk)
            for tag in all_user_tags
        }

        toggle_params = self.request.GET.copy()
        toggle_params["tag_mode"] = "or" if tag_mode == "and" else "and"
        toggle_params.pop("page", None)

        page_params = self.request.GET.copy()
        page_params.pop("page", None)

        popular_tags = (
            Tag.objects.filter(user=self.request.user)
            .annotate(num_tasks=Count("tasks"))
            .filter(num_tasks__gt=0)
            .order_by("-num_tasks")[:5]
        )

        context.update(
            {
                "active_tag_ids": tag_ids,
                "active_tags": active_tags,
                "tag_mode": tag_mode,
                "tag_add_urls": tag_add_urls,
                "tag_remove_urls": tag_remove_urls,
                "clear_tags_url": _build_clear_tags_url(self.request),
                "toggle_tag_mode_url": "?" + toggle_params.urlencode(),
                "task_total": self.get_queryset().count(),
                "user_tags": all_user_tags,
                "page_base_params": page_params.urlencode(),
                "popular_tags": popular_tags,
            }
        )
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

TAG_SORT_OPTIONS = {
    "name": "name",
    "-name": "-name",
    "num_tasks": "num_tasks",
    "-num_tasks": "-num_tasks",
    "created_at": "created_at",
    "-created_at": "-created_at",
}


class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = "tasks/tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        qs = Tag.objects.filter(user=self.request.user).annotate(
            num_tasks=Count("tasks")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if self.request.GET.get("show_unused"):
            qs = qs.filter(num_tasks=0)
        sort = self.request.GET.get("sort", "name")
        qs = qs.order_by(TAG_SORT_OPTIONS.get(sort, "name"))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["color_choices"] = Tag.COLOR_CHOICES
        context["current_sort"] = self.request.GET.get("sort", "name")
        context["current_q"] = self.request.GET.get("q", "")
        context["show_unused"] = bool(self.request.GET.get("show_unused"))

        base_params = self.request.GET.copy()
        base_params.pop("sort", None)
        context["tag_list_base_params"] = base_params.urlencode()

        toggle_unused_params = self.request.GET.copy()
        if toggle_unused_params.get("show_unused"):
            toggle_unused_params.pop("show_unused")
        else:
            toggle_unused_params["show_unused"] = "1"
        toggle_unused_params.pop("page", None)
        context["toggle_unused_url"] = "?" + toggle_unused_params.urlencode()

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


class TagExportView(LoginRequiredMixin, View):
    """CSV export of the user's tags."""

    http_method_names = ["get"]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="tags.csv"'
        writer = csv.writer(response)
        writer.writerow(["name", "color", "task_count", "created_at"])
        tags = (
            Tag.objects.filter(user=request.user)
            .annotate(num_tasks=Count("tasks"))
            .order_by("name")
        )
        for tag in tags:
            writer.writerow(
                [tag.name, tag.color, tag.num_tasks, tag.created_at.isoformat()]
            )
        return response


class TagNameUpdateView(LoginRequiredMixin, View):
    """AJAX endpoint to update a tag's name inline."""

    http_method_names = ["post"]

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        name = data.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Tag name cannot be empty."}, status=400)
        if len(name) > 50:
            return JsonResponse(
                {"error": "Tag name cannot exceed 50 characters."}, status=400
            )

        tag = get_object_or_404(Tag.objects.filter(user=request.user), pk=pk)

        if (
            Tag.objects.filter(user=request.user, name__iexact=name)
            .exclude(pk=pk)
            .exists()
        ):
            return JsonResponse({"error": f"Tag '{name}' already exists."}, status=400)

        tag.name = name
        tag.save(update_fields=["name"])
        return JsonResponse({"name": tag.name})


class TagColorUpdateView(LoginRequiredMixin, View):
    """AJAX endpoint to update a tag's color inline."""

    http_method_names = ["post"]

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        color = data.get("color", "")
        valid_colors = [c[0] for c in Tag.COLOR_CHOICES]
        if color not in valid_colors:
            return JsonResponse({"error": "Invalid color."}, status=400)

        tag = get_object_or_404(Tag.objects.filter(user=request.user), pk=pk)
        tag.color = color
        tag.save(update_fields=["color"])
        return JsonResponse({"color": tag.color})


class TagMergeView(LoginRequiredMixin, View):
    """Merge one tag into another, reassigning all tasks."""

    http_method_names = ["get", "post"]

    def get(self, request, pk):
        source_tag = get_object_or_404(Tag.objects.filter(user=request.user), pk=pk)
        other_tags = (
            Tag.objects.filter(user=request.user)
            .exclude(pk=pk)
            .annotate(num_tasks=Count("tasks"))
            .order_by("name")
        )
        return render(
            request,
            "tasks/tag_merge.html",
            {"source_tag": source_tag, "other_tags": other_tags},
        )

    def post(self, request, pk):
        source_tag = get_object_or_404(Tag.objects.filter(user=request.user), pk=pk)
        target_pk = request.POST.get("target_tag", "")
        target_tag = get_object_or_404(
            Tag.objects.filter(user=request.user), pk=target_pk
        )

        if source_tag.pk == target_tag.pk:
            messages.error(request, "Cannot merge a tag with itself.")
            return redirect("tag-merge", pk=pk)

        for task in source_tag.tasks.all():
            task.tags.add(target_tag)

        source_name = source_tag.name
        source_tag.delete()
        messages.success(
            request, f'Tag "{source_name}" merged into "{target_tag.name}".'
        )
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
