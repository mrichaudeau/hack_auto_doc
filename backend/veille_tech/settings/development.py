"""
Django development settings for veille_tech project.
"""

from .base import *

# Development overrides
DEBUG = True
ALLOWED_HOSTS = ['*']

# Development CORS - allow all origins for easier testing
CORS_ALLOW_ALL_ORIGINS = True

# Development-specific logging
LOGGING['root']['level'] = 'DEBUG'
