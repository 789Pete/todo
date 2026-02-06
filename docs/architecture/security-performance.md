# Security and Performance

## Security Architecture

### Defense in Depth Strategy

```mermaid
graph TB
    User[User Request]

    subgraph "Layer 1: Network"
        HTTPS[HTTPS/TLS]
        WAF[PythonAnywhere Firewall]
    end

    subgraph "Layer 2: Application"
        CSRF[CSRF Protection]
        Auth[Authentication]
        Perm[Authorization]
    end

    subgraph "Layer 3: Input Validation"
        Forms[Django Forms]
        Serial[DRF Serializers]
    end

    subgraph "Layer 4: Data"
        ORM[ORM Parameterized Queries]
        Hash[Password Hashing]
    end

    User --> HTTPS
    HTTPS --> WAF
    WAF --> CSRF
    CSRF --> Auth
    Auth --> Perm
    Perm --> Forms
    Forms --> Serial
    Serial --> ORM
    ORM --> Hash

    style HTTPS fill:#ffcccc
    style CSRF fill:#ffe6cc
    style Auth fill:#fff9cc
    style ORM fill:#ccffcc
```

---

## Authentication Security

### Password Security

**Hashing Algorithm**: Argon2 (Winner of Password Hashing Competition)

**Configuration** (`settings/base.py`):

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Strong minimum
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Password Requirements**:
- ✅ Minimum 12 characters
- ✅ Not similar to username/email
- ✅ Not in common password list
- ✅ Not entirely numeric

### Session Security

**Production Configuration** (`settings/production.py`):

```python
# Session cookies
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# CSRF cookies
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Session backend (database-backed for security)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

**Session Invalidation**:

```python
# Logout view
from django.contrib.auth import logout

def logout_view(request):
    """Properly invalidate session on logout."""
    logout(request)  # Deletes session from database
    request.session.flush()  # Clear session data
    return redirect('login')
```

---

## Input Validation and Sanitization

### Form Validation

**Example**: `apps/tasks/forms.py`

```python
from django import forms
from django.core.exceptions import ValidationError
import bleach

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date']

    def clean_title(self):
        """Validate and sanitize title."""
        title = self.cleaned_data['title']

        # Remove leading/trailing whitespace
        title = title.strip()

        # Ensure not empty
        if not title:
            raise ValidationError("Title cannot be empty")

        # Check length
        if len(title) > 200:
            raise ValidationError("Title too long (max 200 characters)")

        # Sanitize HTML (prevent XSS)
        title = bleach.clean(title, tags=[], strip=True)

        return title

    def clean_description(self):
        """Sanitize description HTML."""
        description = self.cleaned_data['description']

        # Allow limited HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        allowed_attributes = {}

        description = bleach.clean(
            description,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        return description
```

### API Validation

**DRF Serializer Validation**:

```python
from rest_framework import serializers

class TaskSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        """Validate title field."""
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Title cannot be empty")

        if len(value) > 200:
            raise serializers.ValidationError("Title too long")

        # Prevent script injection
        if '<script' in value.lower():
            raise serializers.ValidationError("Invalid characters in title")

        return value

    def validate_tag_ids(self, value):
        """Ensure tags belong to user (prevent privilege escalation)."""
        user = self.context['request'].user
        tags = Tag.objects.filter(id__in=value, user=user)

        if tags.count() != len(value):
            raise serializers.ValidationError(
                "Some tags do not exist or do not belong to you"
            )

        return value
```

---

## SQL Injection Prevention

### ORM Best Practices

**Always use ORM** (parameterized queries):

```python
# ✅ SAFE: ORM uses parameterized queries
Task.objects.filter(title__icontains=user_input)

# ❌ DANGEROUS: Never use f-strings in raw SQL
cursor.execute(f"SELECT * FROM tasks WHERE title LIKE '%{user_input}%'")

# ✅ SAFE: If raw SQL needed, use parameters
from django.db import connection
cursor = connection.cursor()
cursor.execute(
    "SELECT * FROM tasks WHERE title LIKE %s",
    [f"%{user_input}%"]
)
```

**Query Logging** (development):

```python
# settings/development.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

---

## Cross-Site Scripting (XSS) Prevention

### Template Auto-Escaping

**Django templates auto-escape by default**:

```django
{# ✅ SAFE: Auto-escaped #}
<p>{{ task.title }}</p>
{# Renders: &lt;script&gt;alert('XSS')&lt;/script&gt; #}

{# ❌ DANGEROUS: Disables escaping #}
<p>{{ task.title|safe }}</p>
{# Renders: <script>alert('XSS')</script> #}

{# ✅ SAFE: Use safe only for trusted, sanitized HTML #}
<div>{{ sanitized_description|safe }}</div>
```

### Content Security Policy (CSP)

**Production Configuration**:

```python
# settings/production.py
MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    # ... other middleware
]

# CSP settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",  # Alpine.js, vis-network
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Bootstrap requires inline styles
    "https://cdn.jsdelivr.net",
)
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # Prevent clickjacking
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
```

---

## Cross-Site Request Forgery (CSRF) Prevention

### CSRF Token Usage

**In Forms**:

```django
<form method="post" action="{% url 'task-create' %}">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Create Task</button>
</form>
```

**In AJAX Requests**:

```javascript
// Get CSRF token from cookie
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

// Include in fetch request
fetch('/api/tasks/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(taskData),
})
```

**DRF Configuration**:

```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

---

## Authorization and Access Control

### User Isolation

**Ensure users can only access their own data**:

```python
# ✅ CORRECT: Filter by user
class TaskListView(ListView):
    model = Task

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

# ✅ CORRECT: Verify ownership before action
class TaskUpdateView(UpdateView):
    model = Task

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

# ❌ DANGEROUS: No user filtering
class TaskListView(ListView):
    model = Task
    queryset = Task.objects.all()  # Shows all users' tasks!
```

### API Permissions

```python
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if object has user attribute and matches request user
        return hasattr(obj, 'user') and obj.user == request.user

# Usage in viewset
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
```

---

## HTTPS and Transport Security

### HTTPS Configuration (Production)

```python
# settings/production.py

# Redirect all HTTP to HTTPS
SECURE_SSL_REDIRECT = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure proxy headers (PythonAnywhere uses proxy)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
```

---

## Rate Limiting

### API Rate Limiting

**DRF Throttling**:

```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users
        'user': '1000/hour',  # Authenticated users
    }
}
```

**Custom Throttling for Sensitive Endpoints**:

```python
from rest_framework.throttling import UserRateThrottle

class LoginRateThrottle(UserRateThrottle):
    """Stricter throttling for login endpoint."""
    rate = '5/minute'

# Usage in view
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
```

---

## Secrets Management

### Environment Variables

**Never commit secrets to Git**:

```python
# ✅ CORRECT: Use environment variables
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
SENTRY_DSN = os.environ.get('SENTRY_DSN')

# ❌ DANGEROUS: Hardcoded secrets
SECRET_KEY = 'django-insecure-hardcoded-key-12345'
```

**`.env.example` template**:

```bash
# Copy to .env and fill in values
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/db
SENTRY_DSN=https://xxx@sentry.io/xxx
```

**GitHub Secrets** for CI/CD:
- Store secrets in GitHub repository settings
- Access via `${{ secrets.SECRET_NAME }}`

---

## Performance Optimization

### Database Query Optimization

**1. Use select_related for ForeignKey**:

```python
# ❌ BAD: N+1 queries
tasks = Task.objects.all()
for task in tasks:
    print(task.user.username)  # Extra query per task!

# ✅ GOOD: 1 query with JOIN
tasks = Task.objects.select_related('user')
for task in tasks:
    print(task.user.username)  # No extra query
```

**2. Use prefetch_related for ManyToMany**:

```python
# ❌ BAD: N+1 queries
tasks = Task.objects.all()
for task in tasks:
    print(task.tags.all())  # Extra query per task!

# ✅ GOOD: 2 queries total
tasks = Task.objects.prefetch_related('tags')
for task in tasks:
    print(task.tags.all())  # No extra query
```

**3. Use only() and defer()**:

```python
# Fetch only needed fields
tasks = Task.objects.only('id', 'title', 'status')

# Defer large fields
tasks = Task.objects.defer('description')
```

**4. Use annotate() for aggregations**:

```python
from django.db.models import Count

# ✅ GOOD: Single query with aggregation
tags = Tag.objects.annotate(
    task_count=Count('tasks')
).filter(task_count__gt=0)

# ❌ BAD: Separate count query for each tag
tags = Tag.objects.all()
for tag in tags:
    count = tag.tasks.count()  # Extra query per tag!
```

**5. Use bulk operations**:

```python
# ✅ GOOD: Bulk create (single query)
tasks = [Task(title=f"Task {i}", user=user) for i in range(100)]
Task.objects.bulk_create(tasks)

# ❌ BAD: Individual creates (100 queries)
for i in range(100):
    Task.objects.create(title=f"Task {i}", user=user)
```

### Database Indexing

**Indexes for common queries**:

```python
class Task(models.Model):
    # ... fields ...

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),  # Filter: user's todo tasks
            models.Index(fields=['user', 'created_at']),  # Sort: user's recent tasks
            models.Index(fields=['user', 'due_date']),  # Filter: upcoming deadlines
        ]
```

**GIN index for full-text search** (PostgreSQL):

```python
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

class Task(models.Model):
    # ... fields ...
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
```

### Caching Strategy

**Template Fragment Caching**:

```django
{% load cache %}

{% cache 300 task_sidebar request.user.id %}
    <div class="sidebar">
        {# Cached for 5 minutes per user #}
        {% include 'tasks/sidebar.html' %}
    </div>
{% endcache %}
```

**View-Level Caching**:

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    return render(request, 'tasks/task_list.html', {'tasks': tasks})
```

**Low-Level Caching**:

```python
from django.core.cache import cache

def get_user_task_count(user):
    """Get task count with caching."""
    cache_key = f'user_{user.id}_task_count'
    count = cache.get(cache_key)

    if count is None:
        count = Task.objects.filter(user=user).count()
        cache.set(cache_key, count, 60 * 5)  # Cache for 5 minutes

    return count
```

**Cache Configuration** (development: dummy, production: database):

```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# Create cache table: python manage.py createcachetable
```

### Static File Optimization

**WhiteNoise Configuration**:

```python
# settings/production.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise settings
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False
WHITENOISE_MANIFEST_STRICT = True
```

**Benefits**:
- ✅ Gzip/Brotli compression
- ✅ Cache headers (1 year)
- ✅ Hashed filenames for cache busting

### Frontend Performance

**1. Minimize JavaScript**:
- Use Alpine.js (15KB) instead of React (140KB+)
- Load vis-network only on graph page
- Use CDN with integrity hashes

**2. Lazy Loading**:

```html
<!-- Load non-critical JS asynchronously -->
<script src="{% static 'js/graph-viewer.js' %}" defer></script>
```

**3. Image Optimization**:
- Use SVG for icons
- Lazy load images: `<img loading="lazy" />`
- Serve WebP with fallback

---

## Performance Monitoring

### Database Query Monitoring

**Django Debug Toolbar** (development):

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']
```

**Query Logging**:

```python
# Log slow queries (>100ms)
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/slow_queries.log',
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'filters': ['slow_queries'],
        }
    }
}
```

### Application Performance Monitoring

**Sentry Performance Monitoring**:

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    traces_sample_rate=0.1,  # 10% of transactions

    # Performance monitoring
    enable_tracing=True,
)
```

---

## Security Checklist

Before deploying to production:

### Configuration
- ✅ `DEBUG = False`
- ✅ `SECRET_KEY` is unique and secret
- ✅ `ALLOWED_HOSTS` configured
- ✅ HTTPS enabled (`SECURE_SSL_REDIRECT = True`)
- ✅ HSTS enabled
- ✅ CSP headers configured

### Authentication
- ✅ Strong password requirements
- ✅ Argon2 password hashing
- ✅ Session cookies secure (`SESSION_COOKIE_SECURE = True`)
- ✅ CSRF protection enabled

### Authorization
- ✅ User isolation enforced
- ✅ Permission checks in views/APIs
- ✅ Object-level permissions

### Input Validation
- ✅ Form validation
- ✅ Serializer validation
- ✅ HTML sanitization

### Injection Prevention
- ✅ ORM used (no raw SQL)
- ✅ Template auto-escaping
- ✅ Parameterized queries

### Headers
- ✅ `X-Frame-Options: DENY`
- ✅ `X-Content-Type-Options: nosniff`
- ✅ `X-XSS-Protection: 1; mode=block`

### Monitoring
- ✅ Sentry error tracking
- ✅ Failed login monitoring
- ✅ Rate limiting enabled

---

## Performance Benchmarks

### Target Metrics (MVP)

| Metric | Target | Acceptable |
|--------|--------|------------|
| Page load time | < 1s | < 2s |
| API response (p95) | < 500ms | < 1s |
| Database queries per page | < 10 | < 20 |
| Concurrent users | 100 | 50 |

### Optimization Priorities

1. **Critical Path**: Task list view, task creation
2. **High Traffic**: Graph visualization, task updates
3. **Low Priority**: Admin panel, reports

### Load Testing Results (Expected)

```
Scenario: 100 concurrent users
- Requests/second: ~500
- Average response time: 200ms
- 95th percentile: 450ms
- Error rate: < 0.1%
```
