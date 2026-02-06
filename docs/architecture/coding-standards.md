# Coding Standards

## Code Quality Philosophy

All code must be:
1. **Readable**: Clear intent, self-documenting
2. **Maintainable**: Easy to modify and extend
3. **Tested**: Comprehensive test coverage
4. **Secure**: No vulnerabilities, validated inputs
5. **Performant**: Optimized queries, minimal overhead

**Automated enforcement** via ruff (pre-commit hooks).

---

## Python Style Guide

### PEP 8 Compliance (via ruff)

**Enforced automatically** by ruff with these rules:

```toml
[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort (import sorting)
    "DJ",     # flake8-django (Django-specific)
    "N",      # pep8-naming
    "UP",     # pyupgrade (modern Python idioms)
    "C90",    # mccabe (complexity checking)
]
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `user_tasks`, `is_completed` |
| Functions | snake_case | `get_active_tasks()`, `create_tag()` |
| Classes | PascalCase | `TaskSerializer`, `GraphBuilder` |
| Constants | UPPER_SNAKE_CASE | `MAX_TAGS_PER_TASK`, `DEFAULT_STATUS` |
| Private attributes | _leading_underscore | `_internal_cache`, `_build_query()` |
| Django models | PascalCase | `Task`, `Tag`, `User` |
| URL names | kebab-case | `task-list`, `tag-create` |

**Examples**:

```python
# Good
class TaskManager:
    MAX_TITLE_LENGTH = 200

    def __init__(self):
        self._cache = {}

    def get_overdue_tasks(self, user):
        return Task.objects.filter(user=user, due_date__lt=timezone.now())

# Bad
class task_manager:  # Wrong: Should be PascalCase
    max_title_length = 200  # Wrong: Constant should be UPPER_CASE

    def GetOverdueTasks(self, User):  # Wrong: Should be snake_case
        pass
```

### Import Organization (via ruff)

**Automatic sorting** with `ruff check --select I --fix`:

```python
# 1. Standard library imports
import os
import sys
from datetime import datetime, timedelta

# 2. Third-party imports
import pytest
from django.conf import settings
from django.db import models
from rest_framework import serializers

# 3. Local application imports
from apps.tasks.models import Task, Tag
from apps.accounts.models import User
```

**Avoid wildcard imports**:
```python
# Bad
from django.db.models import *

# Good
from django.db.models import Q, F, Count
```

### Line Length and Formatting

**Line length**: 88 characters (Black/ruff default)

**Automatic formatting** via `ruff format`:

```python
# Good - ruff auto-formats this
def create_task_with_tags(
    user: User,
    title: str,
    description: str,
    tags: list[str],
    priority: str = "medium",
) -> Task:
    """Create a task with associated tags."""
    task = Task.objects.create(
        user=user,
        title=title,
        description=description,
        priority=priority,
    )
    tag_objects = Tag.objects.filter(user=user, name__in=tags)
    task.tags.set(tag_objects)
    return task
```

### Type Hints (Recommended)

**Use type hints** for function signatures:

```python
from typing import Optional, List
from django.contrib.auth.models import User

def get_user_tasks(
    user: User,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Task]:
    """
    Get tasks for a user, optionally filtered by status.

    Args:
        user: The user to get tasks for
        status: Optional status filter ('todo', 'in_progress', 'done')
        limit: Maximum number of tasks to return

    Returns:
        List of Task instances
    """
    queryset = Task.objects.filter(user=user)
    if status:
        queryset = queryset.filter(status=status)
    return list(queryset[:limit])
```

---

## Django-Specific Standards

### Model Best Practices

**1. Use UUID primary keys**:
```python
import uuid
from django.db import models

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```

**2. Add `__str__` methods**:
```python
class Task(models.Model):
    # ... fields ...

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
```

**3. Use `Meta` for ordering and indexes**:
```python
class Task(models.Model):
    # ... fields ...

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
```

**4. Add model methods for business logic**:
```python
class Task(models.Model):
    # ... fields ...

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        from django.utils import timezone
        return (
            self.due_date
            and self.due_date < timezone.now().date()
            and self.status != 'done'
        )
```

**5. Use `select_related` and `prefetch_related`**:
```python
# Good: Avoid N+1 queries
tasks = Task.objects.select_related('user').prefetch_related('tags')

# Bad: N+1 query problem
tasks = Task.objects.all()
for task in tasks:
    print(task.user.username)  # Separate query for each task!
    print(task.tags.all())  # Separate query for each task!
```

### View Best Practices

**1. Use class-based views for CRUD**:
```python
from django.views.generic import ListView, CreateView, UpdateView

class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).prefetch_related('tags')
```

**2. Use function-based views for simple logic**:
```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})
```

**3. Always validate user ownership**:
```python
# Good: Ensures user can only access their own tasks
task = get_object_or_404(Task, pk=pk, user=request.user)

# Bad: Security vulnerability (user can access any task)
task = get_object_or_404(Task, pk=pk)
```

### Serializer Best Practices

**1. Validate user ownership in serializers**:
```python
class TaskSerializer(serializers.ModelSerializer):
    def validate_tag_ids(self, value):
        """Ensure all tags belong to the user."""
        user = self.context['request'].user
        tags = Tag.objects.filter(id__in=value, user=user)
        if tags.count() != len(value):
            raise serializers.ValidationError("Some tags do not exist.")
        return value
```

**2. Use `read_only_fields`**:
```python
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

**3. Add computed fields**:
```python
class TaskSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'is_overdue', 'days_until_due']
```

### URL Routing Best Practices

**1. Use meaningful URL names**:
```python
# apps/tasks/urls.py
urlpatterns = [
    path('', views.task_list, name='task-list'),
    path('create/', views.task_create, name='task-create'),
    path('<uuid:pk>/', views.task_detail, name='task-detail'),
]
```

**2. Use `reverse()` instead of hardcoded URLs**:
```python
# Good
from django.urls import reverse

url = reverse('task-detail', kwargs={'pk': task.id})

# Bad
url = f'/tasks/{task.id}/'
```

---

## JavaScript/Frontend Standards

### Alpine.js Conventions

**1. Use declarative syntax**:
```html
<!-- Good: Declarative Alpine.js -->
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>

<!-- Bad: Imperative jQuery-style -->
<div id="container">
    <button onclick="toggleContent()">Toggle</button>
    <div id="content" style="display: none;">Content</div>
</div>
```

**2. Extract complex logic to components**:
```javascript
// static/js/task-manager.js
function taskManager() {
    return {
        tasks: [],
        loading: false,

        async loadTasks() {
            this.loading = true;
            const response = await fetch('/api/tasks/');
            this.tasks = await response.json();
            this.loading = false;
        },

        async createTask(title) {
            const response = await fetch('/api/tasks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ title }),
            });
            const task = await response.json();
            this.tasks.push(task);
        }
    };
}
```

**3. Use CSRF token for POST requests**:
```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### CSS Organization

**1. Use BEM naming**:
```css
/* Block */
.task-card {}

/* Element */
.task-card__title {}
.task-card__description {}

/* Modifier */
.task-card--completed {}
.task-card__title--urgent {}
```

**2. Use CSS variables for theming**:
```css
:root {
    --color-primary: #4ECDC4;
    --color-danger: #FF6B6B;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
}

.task-card {
    padding: var(--spacing-md);
    border: 1px solid var(--color-primary);
}
```

---

## Testing Standards

### Test Organization

**1. Use Factory Boy for test data**:
```python
# apps/tasks/tests/factories.py
import factory
from apps.tasks.models import Task, Tag

class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    status = 'todo'
    priority = 'medium'
    user = factory.SubFactory('apps.accounts.tests.factories.UserFactory')
```

**2. Write descriptive test names**:
```python
# Good: Clear what's being tested
def test_task_is_overdue_when_due_date_past_and_not_done():
    task = TaskFactory(due_date=date.today() - timedelta(days=1), status='todo')
    assert task.is_overdue is True

# Bad: Unclear test purpose
def test_task():
    task = TaskFactory()
    assert task
```

**3. Use pytest fixtures**:
```python
# apps/tasks/tests/conftest.py
import pytest
from apps.tasks.tests.factories import TaskFactory, UserFactory

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def task(user):
    return TaskFactory(user=user)

# Usage in test
def test_task_belongs_to_user(task, user):
    assert task.user == user
```

**4. Test edge cases**:
```python
def test_task_title_cannot_be_empty():
    with pytest.raises(ValidationError):
        task = Task(title='', user=user)
        task.full_clean()

def test_task_can_have_maximum_5_tags():
    task = TaskFactory()
    tags = TagFactory.create_batch(6, user=task.user)
    with pytest.raises(ValidationError):
        task.tags.set(tags)
```

### Test Coverage Goals

**Minimum coverage**: 80%

**Target coverage**:
- Models: 95%+
- Views: 85%+
- API endpoints: 90%+
- Business logic: 95%+
- Templates: 70%+ (Playwright E2E)

**Run coverage**:
```bash
pytest --cov=apps --cov-report=html --cov-report=term
```

---

## Documentation Standards

### Docstring Format (Google Style)

```python
def get_user_tasks(user: User, status: str = None, limit: int = 50) -> list[Task]:
    """
    Get tasks for a user, optionally filtered by status.

    This function retrieves tasks from the database with optimized queries
    to avoid N+1 problems. Tags are prefetched for efficiency.

    Args:
        user: The user to get tasks for
        status: Optional status filter ('todo', 'in_progress', 'done')
        limit: Maximum number of tasks to return

    Returns:
        List of Task instances ordered by creation date (newest first)

    Raises:
        ValueError: If status is not one of the valid choices

    Example:
        >>> user = User.objects.get(username='alice')
        >>> tasks = get_user_tasks(user, status='todo', limit=10)
        >>> len(tasks)
        10
    """
    queryset = Task.objects.filter(user=user).prefetch_related('tags')

    if status:
        valid_statuses = ['todo', 'in_progress', 'done']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        queryset = queryset.filter(status=status)

    return list(queryset[:limit])
```

### Comment Guidelines

**Do comment**:
- Complex business logic
- Non-obvious optimizations
- Workarounds for bugs
- Security considerations

**Don't comment**:
- Obvious code
- What the code does (code should be self-documenting)

```python
# Good: Explains why, not what
# Use select_related to avoid N+1 query problem when accessing user.username
tasks = Task.objects.select_related('user').all()

# Bad: Obvious
# Get all tasks
tasks = Task.objects.all()
```

---

## Security Standards

### Input Validation

**Always validate user input**:

```python
# Good: Validate in form
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status']

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise ValidationError("Title cannot be empty")
        if len(title) > 200:
            raise ValidationError("Title too long")
        return title.strip()

# Good: Validate in serializer
class TaskSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
```

### SQL Injection Prevention

**Always use Django ORM** (parameterized queries):

```python
# Good: ORM prevents SQL injection
Task.objects.filter(title__icontains=user_input)

# Bad: Raw SQL vulnerable to injection
cursor.execute(f"SELECT * FROM tasks WHERE title LIKE '%{user_input}%'")

# If raw SQL is necessary, use parameters
cursor.execute("SELECT * FROM tasks WHERE title LIKE %s", [f"%{user_input}%"])
```

### XSS Prevention

**Django templates auto-escape** by default:

```django
{# Good: Auto-escaped #}
<p>{{ task.title }}</p>

{# Bad: Disables escaping (dangerous) #}
<p>{{ task.title|safe }}</p>

{# Only use |safe for trusted HTML #}
<div>{{ sanitized_html|safe }}</div>
```

### CSRF Protection

**Always include CSRF token** in forms:

```django
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>
```

**Include CSRF token in AJAX**:

```javascript
fetch('/api/tasks/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
})
```

---

## Performance Standards

### Database Query Optimization

**1. Avoid N+1 queries**:
```python
# Good
tasks = Task.objects.prefetch_related('tags')
for task in tasks:
    print(task.tags.all())  # No extra queries

# Bad
tasks = Task.objects.all()
for task in tasks:
    print(task.tags.all())  # N extra queries!
```

**2. Use `only()` and `defer()` for large models**:
```python
# Only fetch needed fields
tasks = Task.objects.only('id', 'title', 'status')
```

**3. Use database indexes**:
```python
class Task(models.Model):
    # ... fields ...

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),  # Frequently filtered together
            models.Index(fields=['-created_at']),  # Frequently ordered
        ]
```

**4. Use `bulk_create()` for multiple inserts**:
```python
# Good
tasks = [Task(title=f"Task {i}", user=user) for i in range(100)]
Task.objects.bulk_create(tasks)

# Bad (100 database queries)
for i in range(100):
    Task.objects.create(title=f"Task {i}", user=user)
```

### Template Performance

**1. Use template fragment caching**:
```django
{% load cache %}

{% cache 300 task_sidebar request.user.id %}
    <div class="sidebar">
        {# Expensive rendering #}
    </div>
{% endcache %}
```

**2. Minimize template logic**:
```django
{# Bad: Complex logic in template #}
{% for task in tasks %}
    {% if task.due_date and task.due_date < today and task.status != 'done' %}
        <span class="overdue">Overdue!</span>
    {% endif %}
{% endfor %}

{# Good: Add property to model #}
{% for task in tasks %}
    {% if task.is_overdue %}
        <span class="overdue">Overdue!</span>
    {% endif %}
{% endfor %}
```

---

## Git Commit Standards

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature or bug fix)
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.

**Examples**:

```
feat: Add status filtering to task list

Implemented status filter dropdown on task list page.
Users can now filter tasks by todo, in_progress, or done status.

Closes #42
```

```
fix: Prevent duplicate tag creation

Added case-insensitive uniqueness check for tag names.
Previously, users could create "Work" and "work" as separate tags.

Fixes #58
```

### Branch Naming

```
feature/short-description
bugfix/short-description
hotfix/short-description
```

**Examples**:
- `feature/task-filtering`
- `bugfix/tag-duplication`
- `hotfix/security-csrf`

---

## Code Review Checklist

Before submitting PR:
- ✅ Code passes `ruff check .`
- ✅ Code passes `ruff format --check .`
- ✅ All tests pass (`pytest`)
- ✅ Test coverage meets minimum (80%)
- ✅ No security vulnerabilities
- ✅ Documentation updated (if needed)
- ✅ Database migrations created (if needed)
- ✅ Commit messages follow standards
- ✅ No commented-out code
- ✅ No debug print statements
- ✅ Environment variables in `.env.example`

For reviewers:
- ✅ Code is readable and maintainable
- ✅ Business logic is correct
- ✅ Edge cases are handled
- ✅ Security best practices followed
- ✅ Performance considerations addressed
- ✅ Tests are comprehensive
- ✅ Documentation is clear
