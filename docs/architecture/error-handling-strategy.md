# Error Handling Strategy

## Error Handling Philosophy

1. **Fail gracefully**: Never expose internal errors to users
2. **Log everything**: Capture context for debugging
3. **User-friendly messages**: Clear, actionable error messages
4. **Consistent responses**: Standardized error formats
5. **Quick recovery**: Provide paths to resolution

---

## Error Categories

### 1. User Errors (4xx)

**Cause**: Invalid input, permissions, not found

**Response**: User-friendly message with guidance

**Examples**:
- 400 Bad Request: Invalid form data
- 401 Unauthorized: Not logged in
- 403 Forbidden: No permission
- 404 Not Found: Resource doesn't exist

### 2. Server Errors (5xx)

**Cause**: Application bugs, database errors, external service failures

**Response**: Generic message, log details, alert developers

**Examples**:
- 500 Internal Server Error: Unhandled exception
- 503 Service Unavailable: Database connection failed

---

## Django View Error Handling

### Standard View Error Handling

```python
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def task_update(request, pk):
    """Update task with comprehensive error handling."""
    try:
        # Get task (404 if not found or not owned by user)
        task = get_object_or_404(Task, pk=pk, user=request.user)

        if request.method == 'POST':
            form = TaskForm(request.POST, instance=task)

            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, 'Task updated successfully!')
                    return redirect('task-detail', pk=task.pk)

                except ValidationError as e:
                    messages.error(request, f'Validation error: {e.message}')
                    logger.warning(
                        f'Task validation error for user {request.user.id}: {e}',
                        extra={'user_id': request.user.id, 'task_id': task.id}
                    )

                except Exception as e:
                    messages.error(request, 'An unexpected error occurred. Please try again.')
                    logger.error(
                        f'Unexpected error updating task: {e}',
                        exc_info=True,
                        extra={'user_id': request.user.id, 'task_id': task.id}
                    )

            else:
                messages.error(request, 'Please correct the errors below.')

        else:
            form = TaskForm(instance=task)

        return render(request, 'tasks/task_form.html', {'form': form, 'task': task})

    except Task.DoesNotExist:
        messages.error(request, 'Task not found or you do not have permission to access it.')
        return redirect('task-list')

    except Exception as e:
        logger.error(
            f'Unexpected error in task_update: {e}',
            exc_info=True,
            extra={'user_id': request.user.id}
        )
        messages.error(request, 'An unexpected error occurred. Our team has been notified.')
        return redirect('task-list')
```

### Custom Error Pages

**404 Error Page** (`templates/404.html`):

```django
{% extends 'base.html' %}

{% block title %}Page Not Found{% endblock %}

{% block content %}
<div class="error-page">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist or you don't have permission to access it.</p>

    <div class="suggestions">
        <h2>What would you like to do?</h2>
        <ul>
            <li><a href="{% url 'task-list' %}">View your tasks</a></li>
            <li><a href="{% url 'home' %}">Go to homepage</a></li>
            <li><a href="{% url 'help' %}">Get help</a></li>
        </ul>
    </div>
</div>
{% endblock %}
```

**500 Error Page** (`templates/500.html`):

```django
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
</head>
<body>
    <h1>500 - Server Error</h1>
    <p>Something went wrong on our end. We've been notified and are working to fix it.</p>
    <p>Please try again in a few minutes.</p>
    <a href="/">Go to homepage</a>
</body>
</html>
```

**Configuration** (`settings/production.py`):

```python
# Custom error handlers
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'

# Custom error views
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)
```

---

## API Error Handling

### DRF Exception Handling

**Custom Exception Handler**:

```python
# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Provides consistent error response format.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize error response format
        custom_response_data = {
            'error': {
                'message': get_error_message(exc),
                'code': get_error_code(exc),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data

    else:
        # Unhandled exception (500 error)
        logger.error(
            f'Unhandled API exception: {exc}',
            exc_info=True,
            extra={
                'view': context.get('view'),
                'request': context.get('request'),
            }
        )

        custom_response_data = {
            'error': {
                'message': 'An unexpected error occurred. Please try again later.',
                'code': 'internal_server_error',
                'details': {}
            }
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response

def get_error_message(exc):
    """Extract user-friendly error message."""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Return first error message
            return str(list(exc.detail.values())[0][0]) if exc.detail else str(exc)
        return str(exc.detail)
    return str(exc)

def get_error_code(exc):
    """Get error code from exception."""
    code_mapping = {
        'NotAuthenticated': 'authentication_required',
        'AuthenticationFailed': 'authentication_failed',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'ValidationError': 'validation_error',
        'Throttled': 'rate_limit_exceeded',
    }
    return code_mapping.get(exc.__class__.__name__, 'error')
```

**Configuration** (`settings/base.py`):

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}
```

### API Error Response Format

**Standard Error Response**:

```json
{
    "error": {
        "message": "Task not found or you do not have permission to access it.",
        "code": "not_found",
        "details": {
            "detail": "Not found."
        }
    }
}
```

**Validation Error Response**:

```json
{
    "error": {
        "message": "Validation failed",
        "code": "validation_error",
        "details": {
            "title": ["This field may not be blank."],
            "tag_ids": ["Task cannot have more than 5 tags."]
        }
    }
}
```

### API Error Handling in ViewSets

```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).prefetch_related('tags')

    def create(self, request, *args, **kwargs):
        """Create task with error handling."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            self.perform_create(serializer)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            logger.warning(
                f'Task creation validation error: {e}',
                extra={'user_id': request.user.id, 'data': request.data}
            )
            raise  # Re-raise to let DRF handle it

        except IntegrityError as e:
            logger.error(
                f'Database integrity error creating task: {e}',
                exc_info=True,
                extra={'user_id': request.user.id}
            )
            raise ValidationError({'detail': 'A task with this title already exists.'})

        except Exception as e:
            logger.error(
                f'Unexpected error creating task: {e}',
                exc_info=True,
                extra={'user_id': request.user.id}
            )
            raise ValidationError({'detail': 'An unexpected error occurred. Please try again.'})

    def perform_create(self, serializer):
        """Save task with user association."""
        serializer.save(user=self.request.user)
```

---

## Form Validation Errors

### Form Error Display

**Template** (`tasks/task_form.html`):

```django
<form method="post">
    {% csrf_token %}

    {# Non-field errors #}
    {% if form.non_field_errors %}
        <div class="alert alert-danger">
            {{ form.non_field_errors }}
        </div>
    {% endif %}

    {# Field-specific errors #}
    {% for field in form %}
        <div class="form-group {% if field.errors %}has-error{% endif %}">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}

            {% if field.errors %}
                <div class="field-errors">
                    {% for error in field.errors %}
                        <p class="error-message">{{ error }}</p>
                    {% endfor %}
                </div>
            {% endif %}

            {% if field.help_text %}
                <small class="form-text">{{ field.help_text }}</small>
            {% endif %}
        </div>
    {% endfor %}

    <button type="submit" class="btn btn-primary">Save Task</button>
</form>
```

### Custom Form Error Messages

```python
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date']
        error_messages = {
            'title': {
                'required': 'Please enter a task title.',
                'max_length': 'Title is too long (maximum 200 characters).',
            },
            'due_date': {
                'invalid': 'Please enter a valid date in YYYY-MM-DD format.',
            }
        }

    def clean_title(self):
        """Custom title validation with clear error messages."""
        title = self.cleaned_data['title']

        if not title.strip():
            raise ValidationError('Title cannot be empty or contain only spaces.')

        if len(title) < 3:
            raise ValidationError('Title must be at least 3 characters long.')

        return title.strip()
```

---

## Database Error Handling

### Transaction Management

```python
from django.db import transaction, IntegrityError

@transaction.atomic
def create_task_with_tags(user, task_data, tag_names):
    """
    Create task with tags in a transaction.
    Rolls back if any operation fails.
    """
    try:
        # Create task
        task = Task.objects.create(
            user=user,
            title=task_data['title'],
            description=task_data.get('description', ''),
        )

        # Create or get tags
        tags = []
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(
                user=user,
                name=tag_name,
                defaults={'color': '#4ECDC4'}
            )
            tags.append(tag)

        # Associate tags with task
        task.tags.set(tags)

        return task

    except IntegrityError as e:
        logger.error(f'Database integrity error: {e}', exc_info=True)
        raise ValidationError('Failed to create task. Please check your data.')

    except Exception as e:
        logger.error(f'Unexpected error creating task: {e}', exc_info=True)
        raise
```

### Connection Error Handling

```python
from django.db import connection, OperationalError

def check_database_connection():
    """Check if database is accessible."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except OperationalError as e:
        logger.critical(f'Database connection failed: {e}', exc_info=True)
        return False
```

---

## Logging Strategy

### Logging Configuration

**Production Logging** (`settings/production.py`):

```python
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        }
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Include context
logger.info(
    'Task created successfully',
    extra={
        'user_id': user.id,
        'task_id': task.id,
        'title': task.title,
    }
)

# ✅ GOOD: Use appropriate log level
logger.debug('Entering task creation flow')  # Detailed debugging
logger.info('Task created')  # Normal operation
logger.warning('Task exceeds recommended tag count')  # Potential issue
logger.error('Failed to create task', exc_info=True)  # Error with traceback
logger.critical('Database connection lost')  # System failure

# ❌ BAD: No context
logger.info('Task created')

# ❌ BAD: Logging sensitive data
logger.info(f'User password: {password}')  # Never log passwords!

# ✅ GOOD: Exception logging with traceback
try:
    task.save()
except Exception as e:
    logger.error('Failed to save task', exc_info=True, extra={'task_id': task.id})
    raise
```

---

## User Feedback Messages

### Django Messages Framework

```python
from django.contrib import messages

def task_create(request):
    """Create task with user feedback."""
    if request.method == 'POST':
        form = TaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user

            try:
                task.save()
                messages.success(request, f'Task "{task.title}" created successfully!')
                return redirect('task-detail', pk=task.pk)

            except Exception as e:
                logger.error(f'Error creating task: {e}', exc_info=True)
                messages.error(request, 'Failed to create task. Please try again.')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form})
```

### Message Display Template

```django
{# templates/includes/messages.html #}
{% if messages %}
    <div class="messages">
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        {% endfor %}
    </div>
{% endif %}
```

**Include in base template**:

```django
{# templates/base.html #}
<body>
    {% include 'includes/messages.html' %}

    {% block content %}{% endblock %}
</body>
```

---

## Frontend Error Handling

### JavaScript Error Handling

```javascript
// static/js/task-manager.js

async function createTask(taskData) {
    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(taskData),
        });

        if (!response.ok) {
            // Handle HTTP errors
            const errorData = await response.json();
            throw new Error(errorData.error?.message || 'Failed to create task');
        }

        const task = await response.json();
        showSuccessMessage('Task created successfully!');
        return task;

    } catch (error) {
        console.error('Error creating task:', error);
        showErrorMessage(error.message);
        throw error;
    }
}

function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.getElementById('messages').appendChild(alertDiv);
}

function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.getElementById('messages').appendChild(alertDiv);
}
```

### Alpine.js Error Handling

```javascript
function taskManager() {
    return {
        tasks: [],
        loading: false,
        error: null,

        async loadTasks() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/api/tasks/');

                if (!response.ok) {
                    throw new Error('Failed to load tasks');
                }

                const data = await response.json();
                this.tasks = data.results;

            } catch (error) {
                console.error('Error loading tasks:', error);
                this.error = 'Failed to load tasks. Please try again.';

            } finally {
                this.loading = false;
            }
        }
    };
}
```

---

## Error Monitoring and Alerting

### Sentry Integration

**Capture custom context**:

```python
from sentry_sdk import capture_exception, capture_message, set_context

try:
    task.save()
except Exception as e:
    # Add context before capturing
    set_context('task', {
        'id': task.id,
        'title': task.title,
        'user_id': task.user_id,
    })
    capture_exception(e)
    raise
```

**Capture custom messages**:

```python
from sentry_sdk import capture_message

# Capture warning
if task.tags.count() > 5:
    capture_message('Task exceeds recommended tag count', level='warning')
```

### Error Rate Thresholds

**Alert when**:
- Error rate > 1% (5-minute window)
- 500 errors > 10/minute
- Database connection failures
- Authentication failures > 50/minute

---

## Recovery Strategies

### Graceful Degradation

```python
def get_task_recommendations(user):
    """Get task recommendations with fallback."""
    try:
        # Try ML-based recommendations
        return ml_recommendation_service.get_recommendations(user)
    except Exception as e:
        logger.warning(f'Recommendation service failed: {e}')
        # Fallback to simple recent tasks
        return Task.objects.filter(user=user).order_by('-created_at')[:5]
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def send_notification(user, message):
    """Send notification with retry logic."""
    # External service call that might fail
    notification_service.send(user.email, message)
```

---

## Error Handling Checklist

Before deploying:
- ✅ Custom 404 and 500 error pages
- ✅ Logging configured (file + Sentry)
- ✅ User-friendly error messages
- ✅ API error responses standardized
- ✅ Database transactions for critical operations
- ✅ Form validation errors displayed
- ✅ Frontend error handling (fetch errors)
- ✅ Error monitoring alerts configured
- ✅ Recovery strategies for external dependencies
