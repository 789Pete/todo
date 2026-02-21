from datetime import date, timedelta

import pytest

from apps.accounts.tests.factories import UserFactory
from apps.tasks.tests.factories import TagFactory, TaskFactory
from apps.visualization.graph_builder import (
    BASE_TAG_SIZE,
    MAX_TAG_SIZE,
    TAG_SIZE_PER_TASK,
    TASK_STATUS_COLORS,
    _darken_hex,
    build_graph_data,
)


@pytest.mark.django_db
class TestBuildGraphData:
    def test_empty_data(self):
        user = UserFactory()
        result = build_graph_data(user)
        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["stats"]["total_tasks"] == 0
        assert result["stats"]["total_tags"] == 0
        assert result["stats"]["filtered_tasks"] == 0
        assert result["stats"]["filtered_tags"] == 0

    def test_task_without_tags(self):
        user = UserFactory()
        TaskFactory(user=user)
        result = build_graph_data(user)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["shape"] == "box"
        assert result["edges"] == []
        assert result["stats"]["filtered_tasks"] == 1
        assert result["stats"]["filtered_tags"] == 0

    def test_task_with_tags(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag2 = TagFactory(user=user)
        task = TaskFactory(user=user, tags=[tag1, tag2])
        result = build_graph_data(user)
        task_nodes = [n for n in result["nodes"] if n["id"] == f"task-{task.id}"]
        tag_nodes = [n for n in result["nodes"] if n["group"] == "tag"]
        assert len(task_nodes) == 1
        assert len(tag_nodes) == 2
        assert len(result["edges"]) == 2

    def test_multiple_tasks_shared_tag(self):
        user = UserFactory()
        shared_tag = TagFactory(user=user)
        task1 = TaskFactory(user=user, tags=[shared_tag])
        task2 = TaskFactory(user=user, tags=[shared_tag])
        result = build_graph_data(user)
        task_nodes = [n for n in result["nodes"] if n["group"] != "tag"]
        tag_nodes = [n for n in result["nodes"] if n["group"] == "tag"]
        assert len(task_nodes) == 2
        assert len(tag_nodes) == 1
        assert len(result["edges"]) == 2
        edge_task_ids = {e["from"] for e in result["edges"]}
        assert f"task-{task1.id}" in edge_task_ids
        assert f"task-{task2.id}" in edge_task_ids

    def test_user_isolation(self):
        user1 = UserFactory()
        user2 = UserFactory()
        TaskFactory(user=user1)
        result = build_graph_data(user2)
        assert result["nodes"] == []
        assert result["stats"]["total_tasks"] == 0

    def test_filter_status(self):
        user = UserFactory()
        TaskFactory(user=user, status="todo")
        TaskFactory(user=user, status="done")
        result = build_graph_data(user, filter_status="done")
        assert result["stats"]["filtered_tasks"] == 1
        assert result["stats"]["total_tasks"] == 2
        assert result["nodes"][0]["group"] == "done"

    def test_filter_tag(self):
        user = UserFactory()
        work_tag = TagFactory(user=user, name="Work")
        personal_tag = TagFactory(user=user, name="Personal")
        TaskFactory(user=user, tags=[work_tag])
        TaskFactory(user=user, tags=[personal_tag])
        result = build_graph_data(user, filter_tag="Work")
        task_nodes = [n for n in result["nodes"] if n["group"] != "tag"]
        assert len(task_nodes) == 1
        assert result["stats"]["filtered_tasks"] == 1

    def test_filter_tag_case_insensitive(self):
        user = UserFactory()
        work_tag = TagFactory(user=user, name="Work")
        TaskFactory(user=user, tags=[work_tag])
        result = build_graph_data(user, filter_tag="work")
        assert result["stats"]["filtered_tasks"] == 1

    def test_task_node_color_todo(self):
        user = UserFactory()
        TaskFactory(user=user, status="todo")
        result = build_graph_data(user)
        node = result["nodes"][0]
        assert node["color"] == TASK_STATUS_COLORS["todo"]

    def test_task_node_color_in_progress(self):
        user = UserFactory()
        TaskFactory(user=user, status="in_progress")
        result = build_graph_data(user)
        node = result["nodes"][0]
        assert node["color"] == TASK_STATUS_COLORS["in_progress"]

    def test_task_node_color_done(self):
        user = UserFactory()
        TaskFactory(user=user, status="done")
        result = build_graph_data(user)
        node = result["nodes"][0]
        assert node["color"] == TASK_STATUS_COLORS["done"]

    def test_stats_counts(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, status="todo", tags=[tag])
        TaskFactory(user=user, status="done")
        result = build_graph_data(user, filter_status="todo")
        assert result["stats"]["total_tasks"] == 2
        assert result["stats"]["total_tags"] == 1
        assert result["stats"]["filtered_tasks"] == 1
        assert result["stats"]["filtered_tags"] == 1

    def test_task_node_structure(self):
        user = UserFactory()
        task = TaskFactory(user=user, status="todo")
        result = build_graph_data(user)
        node = result["nodes"][0]
        assert node["id"] == f"task-{task.id}"
        assert node["label"] == task.title
        assert node["group"] == "todo"
        assert node["shape"] == "box"

    def test_tag_node_structure(self):
        user = UserFactory()
        tag = TagFactory(user=user, name="Work", color="#FF6B6B")
        TaskFactory(user=user, tags=[tag])
        result = build_graph_data(user)
        tag_nodes = [n for n in result["nodes"] if n["group"] == "tag"]
        assert len(tag_nodes) == 1
        tag_node = tag_nodes[0]
        assert tag_node["id"] == f"tag-{tag.id}"
        assert tag_node["label"] == "Work"
        assert tag_node["shape"] == "ellipse"
        assert tag_node["color"]["background"] == "#FF6B6B"

    def test_edge_structure(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user, tags=[tag])  # priority='medium' by default
        result = build_graph_data(user)
        assert len(result["edges"]) == 1
        edge = result["edges"][0]
        assert edge["from"] == f"task-{task.id}"
        assert edge["to"] == f"tag-{tag.id}"
        assert edge["color"] == "#999999"  # medium priority color
        assert edge["width"] == 2  # medium priority width (updated Story 3.3)

    # --- Story 3.3: Priority border width ---

    def test_high_priority_task_has_thick_border(self):
        user = UserFactory()
        TaskFactory(user=user, priority="high")
        result = build_graph_data(user)
        assert result["nodes"][0]["borderWidth"] == 3

    def test_medium_priority_task_has_medium_border(self):
        user = UserFactory()
        TaskFactory(user=user, priority="medium")
        result = build_graph_data(user)
        assert result["nodes"][0]["borderWidth"] == 2

    def test_low_priority_task_has_thin_border(self):
        user = UserFactory()
        TaskFactory(user=user, priority="low")
        result = build_graph_data(user)
        assert result["nodes"][0]["borderWidth"] == 1

    # --- Story 3.3: Overdue font color ---

    def test_overdue_task_has_red_font(self):
        user = UserFactory()
        TaskFactory(
            user=user,
            due_date=date.today() - timedelta(days=1),
            status="todo",
        )
        result = build_graph_data(user)
        assert result["nodes"][0]["font"]["color"] == "#cc0000"

    def test_done_task_not_marked_overdue(self):
        user = UserFactory()
        TaskFactory(
            user=user,
            due_date=date.today() - timedelta(days=1),
            status="done",
        )
        result = build_graph_data(user)
        assert result["nodes"][0]["font"]["color"] != "#cc0000"

    def test_future_due_date_not_overdue(self):
        user = UserFactory()
        TaskFactory(
            user=user,
            due_date=date.today() + timedelta(days=1),
            status="todo",
        )
        result = build_graph_data(user)
        assert result["nodes"][0]["font"]["color"] != "#cc0000"

    def test_no_due_date_not_overdue(self):
        user = UserFactory()
        TaskFactory(user=user, due_date=None, status="todo")
        result = build_graph_data(user)
        assert result["nodes"][0]["font"]["color"] != "#cc0000"

    def test_overdue_tooltip_contains_warning(self):
        user = UserFactory()
        TaskFactory(
            user=user,
            due_date=date.today() - timedelta(days=1),
            status="todo",
        )
        result = build_graph_data(user)
        assert "OVERDUE" in result["nodes"][0]["title"]

    # --- Story 3.3: Tag size ---

    def test_tag_size_scales_with_task_count(self):
        user = UserFactory()
        tag1 = TagFactory(user=user)
        tag5 = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag1])
        TaskFactory.create_batch(5, user=user, tags=[tag5])
        result = build_graph_data(user)
        tag_nodes = {n["id"]: n for n in result["nodes"] if n["group"] == "tag"}
        size1 = tag_nodes[f"tag-{tag1.id}"]["size"]
        size5 = tag_nodes[f"tag-{tag5.id}"]["size"]
        assert size5 > size1

    def test_tag_size_base_for_single_task(self):
        """A tag used by exactly 1 task gets BASE_TAG_SIZE + 1*TAG_SIZE_PER_TASK."""
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, tags=[tag])
        result = build_graph_data(user)
        tag_node = next(n for n in result["nodes"] if n["group"] == "tag")
        assert tag_node["size"] == BASE_TAG_SIZE + TAG_SIZE_PER_TASK  # 18

    def test_tag_size_capped_at_maximum(self):
        """Highly-used tag size is capped at MAX_TAG_SIZE."""
        user = UserFactory()
        tag = TagFactory(user=user)
        # 13 tasks: 15 + 13*3 = 54 > 50, should cap at 50
        TaskFactory.create_batch(13, user=user, tags=[tag])
        result = build_graph_data(user)
        tag_node = next(n for n in result["nodes"] if n["group"] == "tag")
        assert tag_node["size"] == MAX_TAG_SIZE

    # --- Story 3.3: Edge priority ---

    def test_high_priority_edge_is_wide(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, priority="high", tags=[tag])
        result = build_graph_data(user)
        assert result["edges"][0]["width"] == 3

    def test_high_priority_edge_color(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, priority="high", tags=[tag])
        result = build_graph_data(user)
        assert result["edges"][0]["color"] == "#ff9800"

    def test_low_priority_edge_color(self):
        user = UserFactory()
        tag = TagFactory(user=user)
        TaskFactory(user=user, priority="low", tags=[tag])
        result = build_graph_data(user)
        assert result["edges"][0]["color"] == "#cccccc"


class TestDarkenHex:
    def test_darkens_value(self):
        result = _darken_hex("#FF6B6B")
        assert result == "#d74343"

    def test_clamps_at_zero(self):
        result = _darken_hex("#000000")
        assert result == "#000000"

    def test_handles_no_hash(self):
        result = _darken_hex("FF6B6B")
        assert result == "#d74343"

    def test_returns_hex_format(self):
        result = _darken_hex("#4ECDC4")
        assert result.startswith("#")
        assert len(result) == 7
