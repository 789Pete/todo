# Tech Stack

## Overview

The technology stack is optimized for **developer velocity**, **production reliability**, and **PythonAnywhere deployment**. Modern Python tooling (uv + ruff) accelerates development while Django 4.2 LTS provides a stable, battle-tested foundation.

## Complete Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Backend** |
| Backend Language | Python | 3.10+ | Server-side application logic | Django 4.2 requirement, modern language features |
| Web Framework | Django | 4.2 LTS | Web application framework | LTS support until April 2026, comprehensive ecosystem |
| Database | PostgreSQL | 14+ | Primary data store | Robust, excellent Django support, JSON fields |
| ORM | Django ORM | (Django 4.2) | Database abstraction | Built-in, powerful query optimization |
| API Framework | Django REST Framework | 3.14+ | REST API endpoints | Industry standard, excellent serialization |
| **Frontend** |
| JavaScript Framework | Alpine.js | 3.x | Reactive UI interactions | 15KB, no build step, progressive enhancement |
| Graph Visualization | vis-network | 9.x | Network graph rendering | Mature, feature-rich, good performance |
| CSS Framework | Bootstrap | 5.3 | Responsive design system | Familiar, accessible, PythonAnywhere compatible |
| **Development Tools** |
| Package Manager | uv | 0.1+ | Python dependency management | 10-100x faster than pip, modern resolver |
| Code Quality | ruff | 0.1.9+ | Linting and formatting | Replaces black, isort, flake8, pylint - 10-100x faster |
| Build Tool | Django Compressor | 4.4 | CSS/JS minification and bundling | Django-native asset pipeline |
| Bundler | esbuild (via Django Compressor) | esbuild 0.19+ | Fast JavaScript bundling | 100x faster than webpack |
| **Testing** |
| Test Framework | pytest | 7.4+ | Unit and integration testing | More powerful than unittest, great ecosystem |
| Test Factories | Factory Boy | 3.3+ | Test data generation | Clean, maintainable test fixtures |
| E2E Testing | Playwright | 1.40+ | End-to-end browser testing | Fast, reliable, multi-browser support |
| Coverage | pytest-cov | 4.1+ | Code coverage measurement | Integrated with pytest |
| Frontend Testing | Jest | 29.x | JavaScript unit testing | Standard for JS testing |
| **Deployment** |
| Hosting Platform | PythonAnywhere | N/A | Web hosting | PRD requirement, Django-optimized |
| Static File Serving | WhiteNoise | 6.6+ | Static asset serving | Fast, no separate server needed |
| WSGI Server | Gunicorn (via PythonAnywhere) | N/A | Production WSGI server | PythonAnywhere default |
| **Monitoring & Operations** |
| Error Tracking | Sentry | 1.40+ | Error and performance monitoring | Industry standard, excellent Django integration |
| Logging | Python logging + Django | Built-in | Application logging | Structured logging to files/Sentry |
| **Security** |
| Password Hashing | Argon2 | (via argon2-cffi 23.1+) | Secure password storage | Winner of Password Hashing Competition |
| HTTPS | Let's Encrypt (PythonAnywhere) | N/A | SSL/TLS certificates | Free, automated, trusted |
| **Database Tools** |
| Database Driver | psycopg2 | 2.9+ | PostgreSQL adapter | Standard PostgreSQL driver for Python |
| Connection Pooling | pgbouncer (optional) | N/A | Database connection pooling | For scaling beyond MVP |
| **Version Control & CI/CD** |
| Version Control | Git | N/A | Source code management | Industry standard |
| Git Hosting | GitHub | N/A | Repository hosting | Free for private repos, Actions included |
| CI/CD | GitHub Actions | N/A | Automated testing and deployment | Free for public repos, tight integration |

## Modern Python Tooling (Critical)

### uv - Blazing Fast Package Management

**Why uv over pip?**

- **10-100x faster** dependency resolution and installation
- **Deterministic** builds with lock file support
- **Compatible** with pip - drop-in replacement
- **Modern** resolver handles complex dependency trees

**Usage**:

```bash
# Install dependencies (replaces: pip install -r requirements.txt)
uv pip sync requirements/development.txt

# Add a new package (replaces: pip install package-name)
uv pip install package-name

# Compile dependencies (replaces: pip-compile)
uv pip compile requirements/production.in -o requirements/production.txt
```

### ruff - Unified Linting and Formatting

**Why ruff over black + isort + flake8 + pylint?**

- **10-100x faster** than existing tools
- **Replaces 5+ tools** with a single binary
- **Compatible** with existing configs
- **Comprehensive** - 700+ linting rules including Django-specific checks

**What ruff replaces**:

| Old Tool | Purpose | Ruff Equivalent |
|----------|---------|-----------------|
| black | Code formatting | `ruff format` |
| isort | Import sorting | `ruff check --select I` |
| flake8 | Style checking | `ruff check --select E,W,F` |
| pylint | Code quality | `ruff check --select PL` |
| flake8-django | Django checks | `ruff check --select DJ` |

**Configuration** (pyproject.toml):

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "DJ",     # flake8-django (CRITICAL for Django projects)
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "C90",    # mccabe complexity
]
ignore = [
    "E501",   # line too long (let formatter handle it)
]

[tool.ruff.lint.per-file-ignores]
"**/migrations/*.py" = ["E501", "DJ01"]  # Ignore in migrations
"**/tests/*.py" = ["S101"]  # Allow assert in tests
```

## Technology Decision Matrix

### Backend Framework: Django 4.2 LTS

**Alternatives Considered**: Flask, FastAPI

| Criteria | Django | Flask | FastAPI |
|----------|--------|-------|---------|
| Built-in Admin | ✅ Yes | ❌ No | ❌ No |
| ORM | ✅ Powerful | ❌ Need SQLAlchemy | ❌ Need SQLAlchemy |
| Authentication | ✅ Built-in | ❌ Extensions | ❌ Manual |
| Forms | ✅ Built-in | ❌ WTForms | ❌ Pydantic |
| LTS Support | ✅ Until 2026 | ❌ No LTS | ❌ No LTS |
| PythonAnywhere | ✅ Native support | ⚠️ Supported | ⚠️ Supported |

**Winner**: Django - Comprehensive features accelerate MVP development

### Frontend Framework: Alpine.js

**Alternatives Considered**: React, Vue.js, Vanilla JS

| Criteria | Alpine.js | React | Vue.js | Vanilla JS |
|----------|-----------|-------|--------|------------|
| Bundle Size | 15KB | 140KB+ | 80KB+ | 0KB |
| Build Step | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| Learning Curve | Low | High | Medium | Low |
| Django Integration | ✅ Excellent | ⚠️ SPA mode | ⚠️ SPA mode | ✅ Excellent |
| Progressive Enhancement | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |

**Winner**: Alpine.js - Perfect balance of power and simplicity for Django

### Database: PostgreSQL

**Alternatives Considered**: MySQL, SQLite

| Criteria | PostgreSQL | MySQL | SQLite |
|----------|------------|-------|--------|
| Django Support | ✅ Excellent | ✅ Good | ✅ Good |
| JSON Fields | ✅ Full support | ⚠️ Limited | ❌ No |
| Full-Text Search | ✅ Native | ⚠️ Basic | ❌ No |
| Production Ready | ✅ Yes | ✅ Yes | ❌ No (dev only) |
| PythonAnywhere | ✅ Supported | ✅ Supported | ✅ Supported |
| Scalability | ✅ Excellent | ✅ Good | ❌ Limited |

**Winner**: PostgreSQL - Superior features and Django integration

## Dependency Management Strategy

### Requirements Files Structure

```
requirements/
├── base.in              # Core dependencies (uv source files)
├── base.txt             # Compiled core dependencies
├── production.in        # Production-only (extends base.in)
├── production.txt       # Compiled production dependencies
├── development.in       # Development-only (extends production.in)
└── development.txt      # Compiled development dependencies
```

### Compilation Workflow

```bash
# Compile all requirement files
uv pip compile requirements/base.in -o requirements/base.txt
uv pip compile requirements/production.in -o requirements/production.txt
uv pip compile requirements/development.in -o requirements/development.txt

# Install for development
uv pip sync requirements/development.txt

# Install for production
uv pip sync requirements/production.txt
```

## Version Pinning Strategy

| Environment | Strategy | Rationale |
|-------------|----------|-----------|
| Production | **Exact pins** (==) | Reproducible builds, prevent surprises |
| Development | **Compatible pins** (>=,<) | Allow minor updates, faster iteration |
| Dependencies | **Let uv resolve** | Modern resolver handles constraints |

**Example** (requirements/base.in):

```
Django>=4.2,<4.3         # Allow patch updates in 4.2 series
djangorestframework>=3.14,<4.0
psycopg2-binary==2.9.9   # Exact pin for binary stability
argon2-cffi>=23.1,<24.0
```

## Browser Support Matrix

| Browser | Minimum Version | Notes |
|---------|-----------------|-------|
| Chrome | 90+ | Full support (2021+) |
| Firefox | 88+ | Full support (2021+) |
| Safari | 14+ | Full support (2020+) |
| Edge | 90+ | Chromium-based (2021+) |
| Mobile Safari | iOS 14+ | Touch events for graph |
| Mobile Chrome | Android 90+ | Touch events for graph |

**Rationale**: Alpine.js and vis-network require modern JavaScript features (ES2015+)

## Development Environment Requirements

### Minimum Requirements

- **OS**: macOS 11+, Windows 10+, Ubuntu 20.04+
- **Python**: 3.10 or 3.11 (via pyenv recommended)
- **PostgreSQL**: 14+ (local or Docker)
- **Node.js**: 18+ LTS (for Playwright, Jest)
- **Git**: 2.30+

### Recommended Setup

- **Editor**: VS Code with extensions:
  - Python (ms-python.python)
  - Ruff (charliermarsh.ruff)
  - Django Template (batisteo.vscode-django)
  - Playwright Test for VSCode (ms-playwright.playwright)
- **Terminal**: iTerm2 (macOS), Windows Terminal (Windows)
- **Database**: Docker PostgreSQL for consistent environments

## Technology Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| uv is new (2024) | Fallback to pip is trivial (compatible commands) |
| ruff is new (2023) | Excellent pytest compatibility, active development |
| PythonAnywhere limitations | Architecture designed within constraints (no WebSockets, etc.) |
| Alpine.js smaller ecosystem | Well-documented, stable API, active community |
| vis-network performance at scale | Pagination and filtering for large graphs (>500 nodes) |

## Technology Upgrade Path

Post-MVP enhancements:

1. **Redis**: Add for caching and session storage (easy Django integration)
2. **Celery**: Add for background tasks if needed (email, export generation)
3. **CDN**: Move static files to CloudFront or similar
4. **Docker**: Containerize for easier local development
5. **Terraform**: Infrastructure as code if moving off PythonAnywhere
