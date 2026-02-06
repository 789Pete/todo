# API Specification

## API Overview

The API follows **RESTful conventions** using Django REST Framework, providing JSON endpoints for task and tag management, plus a specialized graph data endpoint.

**Base URL**: `/api/`

**Authentication**: Session-based (Django sessions)

**Content Type**: `application/json`

**API Versioning**: Not implemented in MVP (can add `/api/v1/` later)

## Authentication

### Session-Based Authentication

All API endpoints require authentication via Django sessions:

```javascript
// Frontend: Credentials included automatically
fetch('/api/tasks/', {
    method: 'GET',
    credentials: 'same-origin',  // Include session cookie
    headers: {
        'X-CSRFToken': getCookie('csrftoken')  // CSRF protection
    }
})
```

**Unauthenticated Response**:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**Status Code**: `401 Unauthorized`

## Endpoint Summary

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/api/tasks/` | List user's tasks | ✅ |
| POST | `/api/tasks/` | Create new task | ✅ |
| GET | `/api/tasks/{id}/` | Get task details | ✅ |
| PUT | `/api/tasks/{id}/` | Update task (full) | ✅ |
| PATCH | `/api/tasks/{id}/` | Update task (partial) | ✅ |
| DELETE | `/api/tasks/{id}/` | Delete task | ✅ |
| GET | `/api/tags/` | List user's tags | ✅ |
| POST | `/api/tags/` | Create new tag | ✅ |
| GET | `/api/tags/{id}/` | Get tag details | ✅ |
| PUT | `/api/tags/{id}/` | Update tag | ✅ |
| DELETE | `/api/tags/{id}/` | Delete tag | ✅ |
| GET | `/api/graph/data/` | Get graph visualization data | ✅ |

## Task Endpoints

### List Tasks

**Endpoint**: `GET /api/tasks/`

**Description**: Retrieve all tasks for the authenticated user

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by status: todo, in_progress, done |
| priority | string | No | Filter by priority: low, medium, high |
| tag | string | No | Filter by tag name (case-insensitive) |
| search | string | No | Search in title and description |
| ordering | string | No | Sort by field: created_at, due_date, priority, title |

**Example Request**:
```http
GET /api/tasks/?status=todo&priority=high&ordering=-due_date
```

**Response**: `200 OK`

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Complete project proposal",
            "description": "Draft comprehensive proposal for Q1 initiatives",
            "status": "todo",
            "priority": "high",
            "due_date": "2024-02-15",
            "position": 0,
            "tags": [
                {
                    "id": "t1a2g3s4-5678-90ab-cdef-1234567890ab",
                    "name": "Work",
                    "color": "#FF6B6B"
                }
            ],
            "created_at": "2024-02-01T10:30:00Z",
            "updated_at": "2024-02-01T10:30:00Z",
            "is_overdue": false,
            "days_until_due": 14
        },
        {
            "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
            "title": "Review security audit",
            "description": "",
            "status": "in_progress",
            "priority": "high",
            "due_date": null,
            "position": 1,
            "tags": [],
            "created_at": "2024-01-28T14:20:00Z",
            "updated_at": "2024-02-01T09:15:00Z",
            "is_overdue": false,
            "days_until_due": null
        }
    ]
}
```

---

### Create Task

**Endpoint**: `POST /api/tasks/`

**Description**: Create a new task for the authenticated user

**Request Body**:

```json
{
    "title": "Implement user authentication",
    "description": "Add login and registration pages with Django auth",
    "status": "todo",
    "priority": "high",
    "due_date": "2024-02-20",
    "tag_ids": ["t1a2g3s4-5678-90ab-cdef-1234567890ab"]
}
```

**Field Validation**:

| Field | Required | Constraints |
|-------|----------|-------------|
| title | ✅ Yes | 1-200 characters, non-empty |
| description | ❌ No | Max 5000 characters |
| status | ❌ No | One of: todo, in_progress, done (default: todo) |
| priority | ❌ No | One of: low, medium, high (default: medium) |
| due_date | ❌ No | ISO date format (YYYY-MM-DD) |
| tag_ids | ❌ No | Array of tag UUIDs, max 5 tags |

**Response**: `201 Created`

```json
{
    "id": "c3d4e5f6-g7h8-9012-cdef-234567890123",
    "title": "Implement user authentication",
    "description": "Add login and registration pages with Django auth",
    "status": "todo",
    "priority": "high",
    "due_date": "2024-02-20",
    "position": 0,
    "tags": [
        {
            "id": "t1a2g3s4-5678-90ab-cdef-1234567890ab",
            "name": "Work",
            "color": "#FF6B6B"
        }
    ],
    "created_at": "2024-02-01T15:45:00Z",
    "updated_at": "2024-02-01T15:45:00Z",
    "is_overdue": false,
    "days_until_due": 19
}
```

**Error Response**: `400 Bad Request`

```json
{
    "title": ["This field may not be blank."],
    "tag_ids": ["Task cannot have more than 5 tags."]
}
```

---

### Get Task

**Endpoint**: `GET /api/tasks/{id}/`

**Description**: Retrieve a specific task by ID

**Response**: `200 OK`

```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Complete project proposal",
    "description": "Draft comprehensive proposal for Q1 initiatives",
    "status": "todo",
    "priority": "high",
    "due_date": "2024-02-15",
    "position": 0,
    "tags": [
        {
            "id": "t1a2g3s4-5678-90ab-cdef-1234567890ab",
            "name": "Work",
            "color": "#FF6B6B"
        }
    ],
    "created_at": "2024-02-01T10:30:00Z",
    "updated_at": "2024-02-01T10:30:00Z",
    "is_overdue": false,
    "days_until_due": 14,
    "related_tasks": [
        {
            "id": "d4e5f6g7-h8i9-0123-defg-345678901234",
            "title": "Schedule team meeting"
        }
    ]
}
```

**Error Response**: `404 Not Found`

```json
{
    "detail": "Not found."
}
```

---

### Update Task (Full)

**Endpoint**: `PUT /api/tasks/{id}/`

**Description**: Update all fields of a task (requires all fields)

**Request Body**:

```json
{
    "title": "Complete project proposal (UPDATED)",
    "description": "Updated description",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2024-02-16",
    "tag_ids": ["t1a2g3s4-5678-90ab-cdef-1234567890ab"]
}
```

**Response**: `200 OK` (same format as Create Task)

---

### Update Task (Partial)

**Endpoint**: `PATCH /api/tasks/{id}/`

**Description**: Update specific fields of a task

**Request Body**:

```json
{
    "status": "done"
}
```

**Response**: `200 OK` (full task object)

**Common Partial Updates**:

```json
// Mark as done
{"status": "done"}

// Change priority
{"priority": "low"}

// Add tags
{"tag_ids": ["tag1", "tag2", "tag3"]}

// Update position (for drag-and-drop reordering)
{"position": 5}
```

---

### Delete Task

**Endpoint**: `DELETE /api/tasks/{id}/`

**Description**: Permanently delete a task

**Response**: `204 No Content` (empty body)

**Error Response**: `404 Not Found`

---

## Tag Endpoints

### List Tags

**Endpoint**: `GET /api/tags/`

**Description**: Retrieve all tags for the authenticated user with usage statistics

**Response**: `200 OK`

```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "t1a2g3s4-5678-90ab-cdef-1234567890ab",
            "name": "Work",
            "color": "#FF6B6B",
            "created_at": "2024-01-15T08:00:00Z",
            "task_count": 12
        },
        {
            "id": "t2b3c4d5-6789-01ab-cdef-234567890abc",
            "name": "Personal",
            "color": "#4ECDC4",
            "created_at": "2024-01-15T08:00:00Z",
            "task_count": 8
        },
        {
            "id": "t3c4d5e6-7890-12bc-defg-34567890abcd",
            "name": "Urgent",
            "color": "#FFA07A",
            "created_at": "2024-01-16T10:30:00Z",
            "task_count": 3
        }
    ]
}
```

---

### Create Tag

**Endpoint**: `POST /api/tags/`

**Description**: Create a new tag for the authenticated user

**Request Body**:

```json
{
    "name": "Learning",
    "color": "#45B7D1"
}
```

**Field Validation**:

| Field | Required | Constraints |
|-------|----------|-------------|
| name | ✅ Yes | 1-50 characters, unique per user (case-insensitive) |
| color | ❌ No | Valid hex color from predefined choices (default: #4ECDC4) |

**Response**: `201 Created`

```json
{
    "id": "t4d5e6f7-8901-23cd-efgh-4567890abcde",
    "name": "Learning",
    "color": "#45B7D1",
    "created_at": "2024-02-01T16:00:00Z",
    "task_count": 0
}
```

**Error Response**: `400 Bad Request`

```json
{
    "name": ["Tag with this name already exists."]
}
```

---

### Get Tag

**Endpoint**: `GET /api/tags/{id}/`

**Description**: Retrieve a specific tag with tasks

**Response**: `200 OK`

```json
{
    "id": "t1a2g3s4-5678-90ab-cdef-1234567890ab",
    "name": "Work",
    "color": "#FF6B6B",
    "created_at": "2024-01-15T08:00:00Z",
    "task_count": 12,
    "tasks": [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Complete project proposal",
            "status": "todo"
        },
        {
            "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
            "title": "Review security audit",
            "status": "in_progress"
        }
    ]
}
```

---

### Update Tag

**Endpoint**: `PUT /api/tags/{id}/` or `PATCH /api/tags/{id}/`

**Description**: Update tag name or color

**Request Body**:

```json
{
    "name": "Work Projects",
    "color": "#FF6B6B"
}
```

**Response**: `200 OK` (same format as Create Tag)

---

### Delete Tag

**Endpoint**: `DELETE /api/tags/{id}/`

**Description**: Delete a tag (removes from all tasks)

**Response**: `204 No Content`

---

## Graph Visualization Endpoint

### Get Graph Data

**Endpoint**: `GET /api/graph/data/`

**Description**: Get task and tag relationships in vis-network format

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| filter_tag | string | No | Show only tasks with this tag |
| filter_status | string | No | Show only tasks with this status |

**Response**: `200 OK`

```json
{
    "nodes": [
        {
            "id": "task-a1b2c3d4",
            "label": "Complete project proposal",
            "group": "todo",
            "shape": "box",
            "color": {
                "background": "#e3f2fd",
                "border": "#2196f3"
            },
            "title": "Priority: high\nDue: 2024-02-15\nTags: Work"
        },
        {
            "id": "tag-t1a2g3s4",
            "label": "Work",
            "group": "tag",
            "shape": "ellipse",
            "color": {
                "background": "#FF6B6B",
                "border": "#d32f2f"
            },
            "title": "12 tasks"
        }
    ],
    "edges": [
        {
            "from": "task-a1b2c3d4",
            "to": "tag-t1a2g3s4",
            "color": "#999999",
            "width": 1
        }
    ],
    "stats": {
        "total_tasks": 25,
        "total_tags": 5,
        "filtered_tasks": 25,
        "filtered_tags": 5
    }
}
```

**Node Types**:

| Type | Shape | Color Based On |
|------|-------|----------------|
| Task | box | Status (todo=blue, in_progress=yellow, done=green) |
| Tag | ellipse | Tag's color field |

**Edge Rules**:
- Connect task nodes to tag nodes
- No task-to-task or tag-to-tag connections in MVP

---

## Error Responses

### Standard Error Format

```json
{
    "field_name": ["Error message 1", "Error message 2"],
    "non_field_errors": ["General error message"]
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation errors, malformed JSON |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist or doesn't belong to user |
| 500 | Internal Server Error | Server-side error (logged) |

### Validation Error Examples

**Empty Title**:
```json
{
    "title": ["This field may not be blank."]
}
```

**Invalid Status**:
```json
{
    "status": ["\"invalid_status\" is not a valid choice."]
}
```

**Too Many Tags**:
```json
{
    "tag_ids": ["Task cannot have more than 5 tags."]
}
```

**Duplicate Tag Name**:
```json
{
    "name": ["Tag with this name already exists for this user."]
}
```

---

## CORS Configuration

**Not needed for MVP** (frontend served from same domain as API)

**Future consideration**: If separating frontend to different domain:

```python
CORS_ALLOWED_ORIGINS = [
    "https://frontend.example.com",
]
```

---

## Rate Limiting

**MVP Configuration**:
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour

**Headers**:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1612281600
```

**Error Response**: `429 Too Many Requests`

```json
{
    "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## Pagination

**Default**: 50 items per page

**Query Parameters**:
- `page`: Page number (starts at 1)
- `page_size`: Items per page (max 100)

**Example**:
```http
GET /api/tasks/?page=2&page_size=20
```

**Response Format**:
```json
{
    "count": 125,
    "next": "http://localhost:8000/api/tasks/?page=3",
    "previous": "http://localhost:8000/api/tasks/?page=1",
    "results": [...]
}
```

---

## API Serializers (Implementation Reference)

### TaskSerializer

```python
from rest_framework import serializers
from .models import Task, Tag

class TagSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at', 'task_count']

class TaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        max_length=5
    )
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'position', 'tags', 'tag_ids',
            'created_at', 'updated_at', 'is_overdue', 'days_until_due'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_tag_ids(self, value):
        """Ensure all tags belong to the user."""
        user = self.context['request'].user
        tags = Tag.objects.filter(id__in=value, user=user)
        if tags.count() != len(value):
            raise serializers.ValidationError("Some tags do not exist or do not belong to you.")
        return value

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        task = Task.objects.create(**validated_data)
        if tag_ids:
            task.tags.set(Tag.objects.filter(id__in=tag_ids))
        return task

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(Tag.objects.filter(id__in=tag_ids))
        return instance
```
