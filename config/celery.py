# Instagram_Clone/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django settings moduli o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Redis ni backend sifatida ishlatish
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery tasvirlangan vazifalarni topish
app.autodiscover_tasks()
