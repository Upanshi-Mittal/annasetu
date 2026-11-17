"""
AnnaSetu settings — imports the dev profile by default.
Override with DJANGO_SETTINGS_MODULE env var.
"""
from .dev import *  # noqa: F401, F403
