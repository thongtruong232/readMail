from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Đặt biến môi trường để Celery biết dùng settings của Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readmail.settings')

app = Celery('readmail')

# Load config từ settings.py (CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm các task trong ứng dụng Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
