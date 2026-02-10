"""
Test settings for todo_project.

SQLite in-memory, faster password hashing.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# SQLite in-memory for fast test execution
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging noise during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {},
    "root": {
        "level": "CRITICAL",
    },
}
