from __future__ import absolute_import, unicode_literals

# Import app Celery để Django nhận diện
from .celery import app as celery_app

__all__ = ['celery_app']
