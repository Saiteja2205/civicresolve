"""
Django settings used exclusively for automated tests.

This module inherits the normal project settings and replaces the
production password hasher with Django's fast MD5 hasher.

This must never be used for production.
"""

from .settings import *  # noqa: F403,F401


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]