# Development Workflow

## Quick Start (Automated Setup)

We provide an **automated setup script** that gets you from zero to running in under 2 minutes using modern Python tooling (uv + ruff).

### Prerequisites

- **Python 3.10+** (install via [pyenv](https://github.com/pyenv/pyenv))
- **PostgreSQL 14+** (local install or Docker)
- **Node.js 18+** LTS (for Playwright, optional for MVP development)
- **Git 2.30+**

### One-Command Setup

```bash
# Clone and setup in one go
git clone https://github.com/yourusername/django-todo-app.git
cd django-todo-app
bash scripts/setup_dev.sh
```

**What the script does**:
1. ✅ Checks Python version (3.10+)
2. ✅ Installs `uv` (if not already installed)
3. ✅ Creates virtual environment
4. ✅ Installs dependencies with uv (10-100x faster than pip!)
5. ✅ Copies `.env.example` → `.env`
6. ✅ Validates PostgreSQL connection
7. ✅ Runs migrations
8. ✅ Creates superuser (prompts for username/password)
9. ✅ Loads sample data (optional)
10. ✅ Installs pre-commit hooks (ruff formatting/linting)

**Expected output**:
```
🚀 Django To-Do App Development Setup
=====================================

✅ Step 1/10: Python 3.10.12 detected
✅ Step 2/10: Installing uv...
⚡ Step 3/10: Installing dependencies with uv... (3.2s)
✅ Step 4/10: Environment configured
✅ Step 5/10: PostgreSQL connection verified
✅ Step 6/10: Migrations applied
✅ Step 7/10: Superuser created
✅ Step 8/10: Sample data loaded
✅ Step 9/10: Pre-commit hooks installed
✅ Step 10/10: Development server ready!

🎉 Setup complete! Run: python manage.py runserver
```

---

## Manual Setup (Step-by-Step)

If you prefer manual setup or need to troubleshoot:

### Step 1: Install Python 3.10+

**Using pyenv (recommended)**:
```bash
# Install pyenv (macOS)
brew install pyenv

# Install Python 3.10
pyenv install 3.10.12
pyenv local 3.10.12

# Verify
python --version  # Should show Python 3.10.12
```

### Step 2: Install uv (Modern Package Manager)

```bash
# Install uv (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version  # Should show uv 0.1.x
```

**Why uv?**
- 10-100x faster than pip
- Better dependency resolution
- Lock file support
- Compatible with pip (drop-in replacement)

### Step 3: Clone Repository

```bash
git clone https://github.com/yourusername/django-todo-app.git
cd django-todo-app
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 5: Install Dependencies with uv

```bash
# Install development dependencies (includes production + dev tools)
uv pip sync requirements/development.txt

# This installs:
# - Django 4.2
# - DRF, PostgreSQL driver
# - pytest, Playwright, Factory Boy
# - ruff (linting + formatting)
# - Sentry SDK
# - And all dependencies (resolved by uv)
```

**Time comparison**:
- pip: ~45 seconds
- uv: ~3 seconds ⚡

### Step 6: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required `.env` settings**:
```bash
SECRET_KEY=your-secret-key-here-generate-with-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://todo_user:password@localhost:5432/todo_db
```

**Generate SECRET_KEY**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 7: Setup PostgreSQL Database

**Option A: Local PostgreSQL**

```bash
# Create database and user (macOS/Linux)
psql postgres
CREATE DATABASE todo_db;
CREATE USER todo_user WITH PASSWORD 'password';
ALTER ROLE todo_user SET client_encoding TO 'utf8';
ALTER ROLE todo_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE todo_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE todo_db TO todo_user;
\q
```

**Option B: Docker PostgreSQL**

```bash
docker run -d \
  --name todo-postgres \
  -e POSTGRES_DB=todo_db \
  -e POSTGRES_USER=todo_user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:14-alpine
```

### Step 8: Run Migrations

```bash
# Apply database migrations
python manage.py migrate

# Expected output:
# Applying contenttypes.0001_initial... OK
# Applying auth.0001_initial... OK
# Applying accounts.0001_initial... OK
# Applying tasks.0001_initial... OK
# ...
```

### Step 9: Create Superuser

```bash
python manage.py createsuperuser

# Enter:
# Username: admin
# Email: admin@example.com
# Password: (your choice)
```

### Step 10: Load Sample Data (Optional)

```bash
python scripts/populate_test_data.py

# Creates:
# - 5 sample tags
# - 20 sample tasks
# - Various statuses and priorities
```

### Step 11: Install Pre-commit Hooks

```bash
# Install pre-commit (if not already installed)
uv pip install pre-commit

# Install git hooks
pre-commit install

# Now ruff will run automatically on every commit!
```

### Step 12: Run Development Server

```bash
python manage.py runserver

# Visit: http://localhost:8000
# Admin: http://localhost:8000/admin
```

---

## Modern Python Tooling (Critical)

### uv - Package Management

**Replace all `pip` commands with `uv pip`**:

```bash
# Install package
uv pip install package-name

# Install from requirements
uv pip sync requirements/development.txt

# Compile requirements (from .in files)
uv pip compile requirements/base.in -o requirements/base.txt

# Upgrade all packages
uv pip compile --upgrade requirements/base.in -o requirements/base.txt
```

**Requirements file structure**:
```
requirements/
├── base.in              # Core dependencies (hand-written)
├── base.txt             # Compiled with exact versions (uv-generated)
├── production.in        # Extends base.in
├── production.txt       # Compiled
├── development.in       # Extends production.in
└── development.txt      # Compiled
```

**Example `base.in`**:
```
Django>=4.2,<4.3
djangorestframework>=3.14,<4.0
psycopg2-binary>=2.9,<3.0
argon2-cffi>=23.1,<24.0
whitenoise>=6.6,<7.0
```

**Compile workflow**:
```bash
# After editing .in files, recompile
uv pip compile requirements/base.in -o requirements/base.txt
uv pip compile requirements/production.in -o requirements/production.txt
uv pip compile requirements/development.in -o requirements/development.txt

# Then sync to your environment
uv pip sync requirements/development.txt
```

### ruff - Linting and Formatting

**Replaces**: black, isort, flake8, pylint, pyupgrade

**Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort (import sorting)
    "DJ",     # flake8-django (CRITICAL!)
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "C90",    # mccabe complexity
]
ignore = [
    "E501",   # line too long (let formatter handle it)
]

[tool.ruff.lint.per-file-ignores]
"**/migrations/*.py" = ["E501", "DJ01"]
"**/tests/*.py" = ["S101"]
```

**Commands**:

```bash
# Check all files
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Format code (replaces black)
ruff format .

# Check + format in one go
ruff check --fix . && ruff format .
```

**Pre-commit hook** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Install pre-commit**:
```bash
pre-commit install

# Now ruff runs automatically on git commit!
# Manual run: pre-commit run --all-files
```

**Speed comparison** (checking 10,000 files):
- black + isort + flake8: ~60 seconds
- ruff: ~0.5 seconds ⚡

---

## Development Commands

### Common Django Commands

```bash
# Run development server
python manage.py runserver

# Run server on different port
python manage.py runserver 8080

# Run server accessible from network
python manage.py runserver 0.0.0.0:8000

# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic --noinput

# Check for issues
python manage.py check
```

### Testing Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/tasks/tests/test_models.py

# Run specific test function
pytest apps/tasks/tests/test_models.py::test_task_creation

# Run tests in parallel (faster)
pytest -n auto

# Run E2E tests with Playwright
pytest apps/tasks/tests/test_e2e.py

# Open Playwright in headed mode (see browser)
pytest apps/tasks/tests/test_e2e.py --headed
```

### Code Quality Commands

```bash
# Run ruff linting
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Format code
ruff format .

# Check format without changing
ruff format --check .

# Run all pre-commit hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

### Database Commands

```bash
# Backup database
pg_dump todo_db > backup.sql

# Restore database
psql todo_db < backup.sql

# Reset database (WARNING: deletes all data)
python manage.py flush

# Drop and recreate database
dropdb todo_db
createdb todo_db
python manage.py migrate
```

---

## Git Workflow

### Branch Strategy

**Main branches**:
- `main` - Production-ready code
- `develop` - Integration branch (not used in simple workflow)

**Feature branches**:
- `feature/task-filtering` - New features
- `bugfix/tag-duplication` - Bug fixes
- `hotfix/security-patch` - Urgent production fixes

### Commit Workflow

```bash
# Create feature branch
git checkout -b feature/task-filtering

# Make changes
# ... edit files ...

# Stage changes
git add apps/tasks/views.py apps/tasks/templates/

# Commit (pre-commit hooks run automatically!)
git commit -m "Add status filtering to task list view"

# If pre-commit fails, fix issues and commit again
# ruff will auto-fix most issues

# Push to remote
git push origin feature/task-filtering

# Create pull request on GitHub
gh pr create --title "Add task filtering" --body "Implements status and priority filters"
```

### Pre-commit Hook Flow

```mermaid
graph LR
    A[git commit] --> B[Pre-commit hooks run]
    B --> C{ruff check}
    C -->|Issues found| D[Auto-fix]
    D --> E{Still issues?}
    E -->|Yes| F[Commit fails<br/>Fix manually]
    E -->|No| G[Commit succeeds]
    C -->|No issues| G
    F --> A
```

---

## IDE Configuration

### VS Code (Recommended)

**Required Extensions**:
- Python (ms-python.python)
- Ruff (charliermarsh.ruff)
- Django Template (batisteo.vscode-django)
- Playwright Test for VSCode (ms-playwright.playwright)

**`.vscode/settings.json`**:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": false,
    "python.formatting.provider": "none",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        }
    },
    "ruff.path": ["${workspaceFolder}/.venv/bin/ruff"],
    "files.associations": {
        "**/*.html": "django-html"
    }
}
```

**`.vscode/launch.json`** (debugging):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django: runserver",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": ["runserver"],
            "django": true,
            "justMyCode": true
        },
        {
            "name": "Django: pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "django": true
        }
    ]
}
```

### PyCharm

**Interpreter Setup**:
1. Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv/bin/python`

**Django Support**:
1. Settings → Languages & Frameworks → Django
2. Enable Django Support
3. Django project root: `<project_root>`
4. Settings: `todo_project/settings/development.py`
5. Manage script: `manage.py`

**Ruff Integration**:
1. Settings → Tools → External Tools
2. Add new tool:
   - Name: `Ruff Check`
   - Program: `$ProjectFileDir$/.venv/bin/ruff`
   - Arguments: `check --fix $FilePath$`

---

## Environment Management

### Multiple Environments

```bash
# Development (default)
export DJANGO_SETTINGS_MODULE=todo_project.settings.development
python manage.py runserver

# Production (local testing)
export DJANGO_SETTINGS_MODULE=todo_project.settings.production
python manage.py runserver

# Testing
export DJANGO_SETTINGS_MODULE=todo_project.settings.test
pytest
```

### Docker Development (Optional)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: todo_db
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://todo_user:password@db:5432/todo_db
    depends_on:
      - db

volumes:
  postgres_data:
```

**Usage**:
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Troubleshooting

### Common Issues

**Issue: `uv: command not found`**
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal
```

**Issue: `psycopg2` installation fails**
```bash
# Solution: Install PostgreSQL development headers
# macOS:
brew install postgresql

# Ubuntu/Debian:
sudo apt-get install libpq-dev python3-dev

# Then reinstall:
uv pip install psycopg2-binary
```

**Issue: Migrations fail with "relation already exists"**
```bash
# Solution: Reset database
python manage.py migrate --fake-initial
# OR drop and recreate database
```

**Issue: Pre-commit hooks fail**
```bash
# Solution: Update hooks
pre-commit autoupdate
pre-commit install

# Or skip hooks temporarily (not recommended)
git commit --no-verify
```

**Issue: Tests fail with database permission errors**
```bash
# Solution: Grant superuser to test user
psql postgres
ALTER USER todo_user WITH SUPERUSER;
```

---

## Development Best Practices

### Code Quality Checklist

Before committing:
- ✅ Run `ruff check --fix .` (auto-fixes most issues)
- ✅ Run `ruff format .` (formats code)
- ✅ Run `pytest` (all tests pass)
- ✅ Run `python manage.py check` (no Django warnings)
- ✅ Update tests for new features
- ✅ Update docstrings for public functions

### Performance Tips

1. **Use uv for package operations**: 10-100x faster than pip
2. **Enable pytest-xdist**: Run tests in parallel (`pytest -n auto`)
3. **Use `--reuse-db`**: Don't recreate test database every time
4. **Prefetch related objects**: Avoid N+1 queries (`prefetch_related`, `select_related`)
5. **Use ruff**: Instant linting/formatting feedback

### Security Reminders

- ✅ Never commit `.env` file
- ✅ Use environment variables for secrets
- ✅ Keep `SECRET_KEY` secret and unique per environment
- ✅ Use HTTPS in production (PythonAnywhere provides this)
- ✅ Enable CSRF protection (Django default)
- ✅ Validate user input in forms and serializers
