from django.utils import timezone

from apps.tasks.models import Tag, Task

# Task status → vis-network node colors
TASK_STATUS_COLORS = {
    "todo": {"background": "#e3f2fd", "border": "#2196f3"},
    "in_progress": {"background": "#fff8e1", "border": "#ff9800"},
    "done": {"background": "#e8f5e9", "border": "#4caf50"},
}

# Task priority → node border width
PRIORITY_BORDER_WIDTH = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

# Task priority → edge width and color
PRIORITY_EDGE_WIDTH = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

PRIORITY_EDGE_COLOR = {
    "high": "#ff9800",
    "medium": "#999999",
    "low": "#cccccc",
}

# Tag node sizing based on usage frequency
BASE_TAG_SIZE = 15  # minimum ellipse size (pixels)
TAG_SIZE_PER_TASK = 3  # extra pixels per task using this tag
MAX_TAG_SIZE = 50  # cap so large tags don't dominate


def build_graph_data(user, filter_tag=None, filter_status=None):
    """
    Build vis-network graph data for the given user.

    Returns dict: {nodes: [...], edges: [...], stats: {...}}
    """
    tasks = Task.objects.filter(user=user).prefetch_related("tags")

    if filter_status:
        tasks = tasks.filter(status=filter_status)
    if filter_tag:
        tasks = tasks.filter(tags__name__iexact=filter_tag).distinct()

    seen_tag_ids = set()
    task_nodes = []
    edges = []

    today = timezone.now().date()

    for task in tasks:
        task_id = f"task-{task.id}"
        status_color = TASK_STATUS_COLORS.get(task.status, TASK_STATUS_COLORS["todo"])

        is_overdue = bool(
            task.due_date and task.due_date < today and task.status != "done"
        )
        font_cfg = {"color": "#cc0000"} if is_overdue else {"color": "#333333"}

        tooltip_parts = [f"Priority: {task.priority}"]
        if task.due_date:
            due_label = f"Due: {task.due_date}"
            if is_overdue:
                due_label += " ⚠ OVERDUE"
            tooltip_parts.append(due_label)
        tag_names = [t.name for t in task.tags.all()]
        if tag_names:
            tooltip_parts.append(f"Tags: {', '.join(tag_names)}")

        task_nodes.append(
            {
                "id": task_id,
                "label": task.title,
                "group": task.status,
                "shape": "box",
                "color": status_color,
                "title": "\n".join(tooltip_parts),
                "borderWidth": PRIORITY_BORDER_WIDTH.get(task.priority, 2),
                "font": font_cfg,
            }
        )

        for tag in task.tags.all():
            tag_id = f"tag-{tag.id}"
            edges.append(
                {
                    "from": task_id,
                    "to": tag_id,
                    "width": PRIORITY_EDGE_WIDTH.get(task.priority, 1),
                    "color": PRIORITY_EDGE_COLOR.get(task.priority, "#999999"),
                }
            )
            seen_tag_ids.add(tag.id)

    tag_nodes = []
    if seen_tag_ids:
        tags = Tag.objects.filter(id__in=seen_tag_ids).prefetch_related("tasks")
        for tag in tags:
            task_count = tag.tasks.filter(user=user).count()
            tag_nodes.append(
                {
                    "id": f"tag-{tag.id}",
                    "label": tag.name,
                    "group": "tag",
                    "shape": "ellipse",
                    "color": {
                        "background": tag.color,
                        "border": _darken_hex(tag.color),
                    },
                    "title": f"{task_count} task{'s' if task_count != 1 else ''}",
                    "size": min(
                        BASE_TAG_SIZE + task_count * TAG_SIZE_PER_TASK, MAX_TAG_SIZE
                    ),
                }
            )

    total_tasks = Task.objects.filter(user=user).count()
    total_tags = Tag.objects.filter(user=user).count()

    return {
        "nodes": task_nodes + tag_nodes,
        "edges": edges,
        "stats": {
            "total_tasks": total_tasks,
            "total_tags": total_tags,
            "filtered_tasks": len(task_nodes),
            "filtered_tags": len(tag_nodes),
        },
    }


def _darken_hex(hex_color):
    """Return a slightly darker version of a hex color for borders."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = max(0, r - 40), max(0, g - 40), max(0, b - 40)
    return f"#{r:02x}{g:02x}{b:02x}"
