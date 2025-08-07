# DropFeed - Django Podcast App

A minimal Django app for uploading MP3 files and publishing them as a podcast RSS feed.

## Features

- Upload MP3 recordings with name and description
- Automatic RSS feed generation
- Django admin integration
- Single-user system with authentication
- Public feed access via configurable URL

## Installation

1. Add `'dropfeed'` to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... your other apps
    'constance',
    'constance.backends.database',
    'dropfeed',
]
```

2. Add constance configuration to your settings.py:
```python
from dropfeed.config import CONSTANCE_CONFIG, CONSTANCE_CONFIG_FIELDSETS

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = CONSTANCE_CONFIG
CONSTANCE_CONFIG_FIELDSETS = CONSTANCE_CONFIG_FIELDSETS
```

3. Include the app URLs in your main urls.py:
```python
from django.urls import path, include

urlpatterns = [
    # ... your other URLs
    path('podcast/', include('dropfeed.urls')),
]
```

4. Run migrations:
```bash
python manage.py makemigrations dropfeed
python manage.py migrate
```

5. Configure media files in settings.py:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

## Dependencies

- Django
- django-constance

Install with: `pip install django-constance`

## Usage

1. Navigate to `/podcast/` to access the upload interface (requires authentication)
2. Configure podcast settings in Django admin under "Constance Config"
3. Share the RSS feed URL with podcast applications

## Security

- Upload interface requires Django authentication
- RSS feed is publicly accessible
- Files are automatically deleted when recordings are removed via admin