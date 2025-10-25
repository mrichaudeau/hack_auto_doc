# -*- coding: utf-8 -*-
"""
Config package initialization.
This ensures Celery app is loaded when Django starts.
"""

# Import Celery app so it's always imported when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
