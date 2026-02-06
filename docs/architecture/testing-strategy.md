# Testing Strategy

## Testing Philosophy

**Test Pyramid**:
```
           /\
          /  \
         / E2E\     ← Few (10-20 tests)
        /------\
       /  Integ \   ← Some (50-100 tests)
      /----------\
     /    Unit    \ ← Many (200+ tests)
    /--------------\
```

**Coverage Goals**:
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Critical user paths
- **E2E Tests**: Core user journeys

**Test Quality > Test Quantity**

---

## Test Stack

| Type | Framework | Purpose |
|------|-----------|---------|
| Unit Tests | pytest | Test individual functions/classes |
| Integration Tests | pytest + Django TestCase | Test component interactions |
| API Tests | pytest + DRF APIClient | Test REST endpoints |
| E2E Tests | Playwright | Test full user journeys |
| Test Data | Factory Boy | Generate realistic test data |
| Coverage | pytest-cov | Measure test coverage |
| Mocking | pytest-mock | Mock external dependencies |

---

## Unit Testing

### Test File Organization

```
apps/tasks/tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── factories.py          # Factory Boy factories
├── test_models.py        # Model tests
├── test_views.py         # View tests
├── test_api.py           # API tests
├── test_serializers.py   # Serializer tests
└── test_permissions.py   # Permission tests
```

### Model Tests

**Test**: `apps/tasks/tests/test_models.py`

```python
import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from apps.tasks.models import Task, Tag
from apps.tasks.tests.factories import TaskFactory, TagFactory, UserFactory

@pytest.mark.django_db
class TestTaskModel:
    """Tests for Task model."""

    def test_task_creation(self):
        """Test basic task creation."""
        user = UserFactory()
        task = TaskFactory(user=user, title="Test Task")

        assert task.title == "Test Task"
        assert task.user == user
        assert task.status == "todo"  # Default status

    def test_task_str_representation(self):
        """Test task __str__ method."""
        task = TaskFactory(title="My Task", status="in_progress")
        assert str(task) == "My Task (In Progress)"

    def test_is_overdue_property(self):
        """Test is_overdue property returns correct value."""
        # Overdue task
        overdue_task = TaskFactory(
            due_date=date.today() - timedelta(days=1),
            status="todo"
        )
        assert overdue_task.is_overdue is True

        # Not overdue (due date in future)
        future_task = TaskFactory(
            due_date=date.today() + timedelta(days=1),
            status="todo"
        )
        assert future_task.is_overdue is False

        # Not overdue (completed)
        completed_task = TaskFactory(
            due_date=date.today() - timedelta(days=1),
            status="done"
        )
        assert completed_task.is_overdue is False

    def test_days_until_due_property(self):
        """Test days_until_due property calculates correctly."""
        task = TaskFactory(due_date=date.today() + timedelta(days=5))
        assert task.days_until_due == 5

        task_no_due_date = TaskFactory(due_date=None)
        assert task_no_due_date.days_until_due is None

    def test_task_tag_relationship(self):
        """Test ManyToMany relationship with tags."""
        task = TaskFactory()
        tags = TagFactory.create_batch(3, user=task.user)

        task.tags.set(tags)
        assert task.tags.count() == 3
        assert list(task.tags.all()) == tags

    def test_task_max_tags_validation(self):
        """Test task cannot have more than 5 tags."""
        task = TaskFactory()
        tags = TagFactory.create_batch(6, user=task.user)

        with pytest.raises(ValidationError, match="cannot have more than 5 tags"):
            task.tags.set(tags)
            task.full_clean()

@pytest.mark.django_db
class TestTagModel:
    """Tests for Tag model."""

    def test_tag_creation(self):
        """Test basic tag creation."""
        user = UserFactory()
        tag = TagFactory(user=user, name="Work")

        assert tag.name == "Work"
        assert tag.user == user

    def test_tag_name_unique_per_user(self):
        """Test tag names are unique per user (case-insensitive)."""
        user = UserFactory()
        TagFactory(user=user, name="Work")

        # Same name, same user → should fail
        with pytest.raises(ValidationError):
            duplicate = Tag(user=user, name="work")  # Case-insensitive
            duplicate.full_clean()

    def test_tag_name_can_duplicate_across_users(self):
        """Test tag names can be same for different users."""
        user1 = UserFactory()
        user2 = UserFactory()

        tag1 = TagFactory(user=user1, name="Work")
        tag2 = TagFactory(user=user2, name="Work")

        assert tag1.name == tag2.name
        assert tag1.user != tag2.user

    def test_tag_task_count_property(self):
        """Test task_count property."""
        tag = TagFactory()
        TaskFactory.create_batch(3, user=tag.user, tags=[tag])

        assert tag.task_count == 3
```

### Factory Boy Factories

**File**: `apps/tasks/tests/factories.py`

```python
import factory
from factory.django import DjangoModelFactory
from datetime import date, timedelta
from apps.tasks.models import Task, Tag
from apps.accounts.models import User

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag{n}")
    color = "#4ECDC4"
    user = factory.SubFactory(UserFactory)

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    status = 'todo'
    priority = 'medium'
    due_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Handle tags ManyToMany relationship."""
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)
```

---

## Integration Testing

### View Tests

**Test**: `apps/tasks/tests/test_views.py`

```python
import pytest
from django.urls import reverse
from apps.tasks.tests.factories import TaskFactory, UserFactory

@pytest.mark.django_db
class TestTaskListView:
    """Tests for task list view."""

    def test_task_list_requires_authentication(self, client):
        """Test unauthenticated users are redirected."""
        url = reverse('task-list')
        response = client.get(url)

        assert response.status_code == 302
        assert '/login/' in response.url

    def test_task_list_shows_only_user_tasks(self, client):
        """Test users only see their own tasks."""
        user1 = UserFactory()
        user2 = UserFactory()

        user1_tasks = TaskFactory.create_batch(3, user=user1)
        user2_tasks = TaskFactory.create_batch(2, user=user2)

        client.force_login(user1)
        url = reverse('task-list')
        response = client.get(url)

        assert response.status_code == 200
        tasks_in_context = list(response.context['tasks'])

        assert len(tasks_in_context) == 3
        for task in user1_tasks:
            assert task in tasks_in_context
        for task in user2_tasks:
            assert task not in tasks_in_context

    def test_task_list_filter_by_status(self, client):
        """Test filtering tasks by status."""
        user = UserFactory()
        TaskFactory.create_batch(2, user=user, status='todo')
        TaskFactory.create_batch(3, user=user, status='done')

        client.force_login(user)
        url = reverse('task-list') + '?status=done'
        response = client.get(url)

        tasks = list(response.context['tasks'])
        assert len(tasks) == 3
        assert all(task.status == 'done' for task in tasks)

@pytest.mark.django_db
class TestTaskCreateView:
    """Tests for task creation view."""

    def test_create_task_success(self, client):
        """Test successful task creation."""
        user = UserFactory()
        client.force_login(user)

        url = reverse('task-create')
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'status': 'todo',
            'priority': 'high',
        }
        response = client.post(url, data)

        assert response.status_code == 302  # Redirect after success
        assert Task.objects.filter(user=user, title='New Task').exists()

    def test_create_task_invalid_data(self, client):
        """Test task creation with invalid data shows errors."""
        user = UserFactory()
        client.force_login(user)

        url = reverse('task-create')
        data = {'title': ''}  # Empty title (invalid)
        response = client.post(url, data)

        assert response.status_code == 200  # Stay on form
        assert 'form' in response.context
        assert response.context['form'].errors
```

---

## API Testing

### API Endpoint Tests

**Test**: `apps/tasks/tests/test_api.py`

```python
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.tasks.tests.factories import TaskFactory, TagFactory, UserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestTaskAPI:
    """Tests for Task API endpoints."""

    def test_list_tasks_requires_authentication(self, api_client):
        """Test API requires authentication."""
        url = reverse('api-task-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tasks_returns_only_user_tasks(self, api_client):
        """Test API returns only authenticated user's tasks."""
        user1 = UserFactory()
        user2 = UserFactory()

        TaskFactory.create_batch(3, user=user1)
        TaskFactory.create_batch(2, user=user2)

        api_client.force_authenticate(user=user1)
        url = reverse('api-task-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_task_success(self, api_client):
        """Test successful task creation via API."""
        user = UserFactory()
        tag = TagFactory(user=user)

        api_client.force_authenticate(user=user)
        url = reverse('api-task-list')
        data = {
            'title': 'API Task',
            'description': 'Created via API',
            'status': 'todo',
            'priority': 'high',
            'tag_ids': [str(tag.id)],
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'API Task'
        assert len(response.data['tags']) == 1

    def test_create_task_with_invalid_tag(self, api_client):
        """Test creating task with tag that doesn't belong to user."""
        user1 = UserFactory()
        user2 = UserFactory()
        other_users_tag = TagFactory(user=user2)

        api_client.force_authenticate(user=user1)
        url = reverse('api-task-list')
        data = {
            'title': 'Task',
            'tag_ids': [str(other_users_tag.id)],  # Tag belongs to user2!
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tag_ids' in response.data

    def test_update_task_partial(self, api_client):
        """Test partial update (PATCH) of task."""
        user = UserFactory()
        task = TaskFactory(user=user, status='todo')

        api_client.force_authenticate(user=user)
        url = reverse('api-task-detail', kwargs={'pk': task.id})
        data = {'status': 'done'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'done'

        task.refresh_from_db()
        assert task.status == 'done'

    def test_delete_task_success(self, api_client):
        """Test successful task deletion."""
        user = UserFactory()
        task = TaskFactory(user=user)

        api_client.force_authenticate(user=user)
        url = reverse('api-task-detail', kwargs={'pk': task.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task.id).exists()

    def test_cannot_access_other_users_task(self, api_client):
        """Test user cannot access another user's task."""
        user1 = UserFactory()
        user2 = UserFactory()
        user2_task = TaskFactory(user=user2)

        api_client.force_authenticate(user=user1)
        url = reverse('api-task-detail', kwargs={'pk': user2_task.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestGraphAPI:
    """Tests for graph visualization API."""

    def test_graph_data_structure(self, api_client):
        """Test graph API returns correct data structure."""
        user = UserFactory()
        tag = TagFactory(user=user)
        task = TaskFactory(user=user)
        task.tags.add(tag)

        api_client.force_authenticate(user=user)
        url = reverse('api-graph-data')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'nodes' in response.data
        assert 'edges' in response.data
        assert 'stats' in response.data

        # Check nodes
        nodes = response.data['nodes']
        assert len(nodes) == 2  # 1 task + 1 tag

        # Check edges
        edges = response.data['edges']
        assert len(edges) == 1  # 1 task-tag connection
```

---

## End-to-End Testing (Playwright)

### E2E Test Setup

**File**: `apps/tasks/tests/test_e2e.py`

```python
import pytest
from playwright.sync_api import Page, expect
from apps.tasks.tests.factories import UserFactory

@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    """Configure Playwright browser context."""
    return {
        **browser_context_args,
        'viewport': {'width': 1920, 'height': 1080},
    }

@pytest.mark.django_db
class TestTaskUserJourney:
    """E2E tests for complete user journeys."""

    def test_create_task_and_add_tags(self, page: Page, live_server):
        """Test user can create task and add tags."""
        # Setup: Create user
        user = UserFactory(username='testuser', password='password123')

        # Step 1: Login
        page.goto(f'{live_server.url}/login/')
        page.fill('input[name="username"]', 'testuser')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')

        expect(page).to_have_url(f'{live_server.url}/')

        # Step 2: Navigate to task creation
        page.click('text=New Task')
        expect(page).to_have_url(f'{live_server.url}/tasks/create/')

        # Step 3: Fill task form
        page.fill('input[name="title"]', 'E2E Test Task')
        page.fill('textarea[name="description"]', 'Created via Playwright')
        page.select_option('select[name="priority"]', 'high')

        # Step 4: Create new tag
        page.click('text=Add Tag')
        page.fill('input[name="tag_name"]', 'Automated')
        page.click('button:has-text("Create Tag")')

        # Step 5: Submit task
        page.click('button[type="submit"]')

        # Verify: Task appears in list
        expect(page).to_have_url(f'{live_server.url}/tasks/')
        expect(page.locator('text=E2E Test Task')).to_be_visible()
        expect(page.locator('text=Automated')).to_be_visible()

    def test_visualize_task_network(self, page: Page, live_server):
        """Test user can visualize task network graph."""
        # Setup
        user = UserFactory(username='testuser', password='password123')
        # ... create some tasks and tags ...

        # Login
        page.goto(f'{live_server.url}/login/')
        page.fill('input[name="username"]', 'testuser')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')

        # Navigate to graph view
        page.click('text=Visualize')
        expect(page).to_have_url(f'{live_server.url}/visualize/')

        # Wait for graph to render
        page.wait_for_selector('#network-graph')

        # Verify graph elements
        graph = page.locator('#network-graph')
        expect(graph).to_be_visible()

        # Test: Click a node (should show details)
        page.evaluate('''
            () => {
                const canvas = document.querySelector('#network-graph canvas');
                canvas.dispatchEvent(new MouseEvent('click', {
                    clientX: 500,
                    clientY: 500
                }));
            }
        ''')

        # Verify: Task details modal appears
        expect(page.locator('.task-details-modal')).to_be_visible()
```

### Playwright Configuration

**File**: `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = todo_project.settings.test
addopts =
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --browser chromium
    --headed false
    --slowmo 0
```

---

## Test Fixtures (Shared)

**File**: `tests/conftest.py`

```python
import pytest
from rest_framework.test import APIClient
from apps.tasks.tests.factories import UserFactory

@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory()

@pytest.fixture
def authenticated_user(user):
    """Create and return an authenticated user."""
    return user

@pytest.fixture
def client(authenticated_user):
    """Django test client with authenticated user."""
    from django.test import Client
    client = Client()
    client.force_login(authenticated_user)
    return client

@pytest.fixture
def api_client(authenticated_user):
    """DRF API client with authenticated user."""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client

@pytest.fixture
def live_server_url(live_server):
    """Return the URL of the live test server."""
    return live_server.url
```

---

## Test Execution

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/tasks/tests/test_models.py

# Run specific test class
pytest apps/tasks/tests/test_models.py::TestTaskModel

# Run specific test function
pytest apps/tasks/tests/test_models.py::TestTaskModel::test_task_creation

# Run E2E tests only
pytest apps/tasks/tests/test_e2e.py

# Run E2E tests in headed mode (see browser)
pytest apps/tasks/tests/test_e2e.py --headed

# Run tests in parallel (faster)
pytest -n auto
```

### Continuous Integration

**GitHub Actions** (`.github/workflows/ci.yml`):

```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=apps --cov-report=xml --cov-report=term
    pytest apps/tasks/tests/test_e2e.py --browser chromium
```

---

## Test Data Management

### Using Factories

```python
# Create single instance
task = TaskFactory()

# Create with specific attributes
task = TaskFactory(title='Specific Title', status='done')

# Create batch
tasks = TaskFactory.create_batch(10, user=user)

# Create with related objects
tag = TagFactory(user=user)
task = TaskFactory(user=user, tags=[tag])
```

### Database Reset

```python
@pytest.fixture(autouse=True)
def reset_db(db):
    """Reset database after each test."""
    yield
    # Cleanup happens automatically with pytest-django
```

---

## Coverage Reporting

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=apps --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals by Component

| Component | Target | Rationale |
|-----------|--------|-----------|
| Models | 95%+ | Critical business logic |
| Views | 85%+ | User-facing functionality |
| API | 90%+ | External interface |
| Serializers | 90%+ | Data validation |
| Forms | 85%+ | Input validation |
| Templates | 70%+ | Via E2E tests |

---

## Performance Testing

### Load Testing (Optional, Post-MVP)

```python
from locust import HttpUser, task, between

class TodoUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Login before starting tasks."""
        self.client.post('/login/', {
            'username': 'testuser',
            'password': 'password123'
        })

    @task(3)
    def view_tasks(self):
        """View task list (most common action)."""
        self.client.get('/tasks/')

    @task(1)
    def create_task(self):
        """Create a new task."""
        self.client.post('/api/tasks/', json={
            'title': 'Load Test Task',
            'status': 'todo'
        })
```

**Run load test**:
```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## Test Maintenance

### Keep Tests Fast

- Use `pytest-xdist` for parallel execution
- Use `--reuse-db` to avoid recreating database
- Mock external services (email, APIs)
- Use `pytest.mark.slow` for slow tests

```python
@pytest.mark.slow
def test_expensive_operation():
    # Long-running test
    pass

# Run without slow tests
# pytest -m "not slow"
```

### Avoid Test Flakiness

- Don't rely on specific ordering
- Use factories instead of fixtures for data
- Avoid `sleep()` in E2E tests (use `wait_for_selector`)
- Mock time-dependent code

```python
# Bad: Flaky test
def test_task_created_today():
    task = TaskFactory()
    assert task.created_at.date() == date.today()  # Flaky at midnight!

# Good: Freeze time
@freeze_time("2024-02-01 12:00:00")
def test_task_created_today():
    task = TaskFactory()
    assert task.created_at.date() == date(2024, 2, 1)
```
