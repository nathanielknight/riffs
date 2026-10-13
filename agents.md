# Riffs Project - Agent Documentation

## Project Overview

**Riffs** is a personal content management system built with Django. It provides functionality through modular Django apps called "riffs", each providing a feature like bookmarking, file-sharing, etc. Some riffs provide features via the Django admin and don't add any non-admin views.

**Key Information:**
- Python, Django, server rendered HTML
- SQLite with FTS5 full-text search
- uv for dev tooling

## Architecture

### Project Structure

```
riffs/
├── riffs/                    # Main project configuration
│   ├── settings.py          # Django settings with security hardening
│   ├── urls.py              # Root URL router
│   └── views.py             # Index view (lists public riffs)
├── bookmarks/               # Bookmark manager riff
├── dropfeed/                # Podcast RSS feed riff
├── quotes/                  # Quotation manager riff (admin-only)
├── templates/               # Shared templates (base.html, index.html)
├── static/                  # CSS (simple.min.css - minimalist styling)
├── Dockerfile               # Docker configuration
└── pyproject.toml           # Project metadata and dependencies
```


## The Riffs (Django Apps)

- Bookmarks (save and search links with tags and descriptions)
- Dropfeed (generate a podcast feed from uploaded audio files)
- Quotes (admin-only database editing riff)

**RSS Feed Implementation:**
See `dropfeed/views.py:34-81` for RSS generation logic. Uses Django's `Rss201rev2Feed` with custom iTunes namespace extensions.

**Important Notes:**
- Feed URL is secure and should not be guessable (uses `secrets.token_urlsafe(16)`)
- Audio files are served directly from media directory
- File size is calculated on upload and stored for RSS enclosure tag


## Development Patterns

### Full-Text Search Pattern

All FTS5 implementations follow this pattern:
1. Create virtual table using raw SQL: `CREATE VIRTUAL TABLE <name>_fts USING fts5(...)`
2. Populate with `INSERT INTO <name>_fts SELECT ...`
3. Query with `SELECT ... FROM <name>_fts WHERE <name>_fts MATCH ?`

See examples:
- bookmarks/views.py:13-27
- quotes/models.py:17-26

### Authentication Pattern

Views use Django's `@login_required` decorator for authenticated endpoints:
```python
from django.contrib.auth.decorators import login_required

@login_required
def create_bookmark(request):
    # Only accessible to logged-in users
```

Public views (like RSS feeds, bookmark index) have no authentication.

### Django Admin Customization

Each app customizes its admin interface in `admin.py`:
- List display fields
- Search fields
- Filter options
- Ordering

Example: `bookmarks/admin.py:5-9`, `dropfeed/admin.py:4-12`

### URL Patterns

Each riff has its own `urls.py` included in main `riffs/urls.py`:
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bookmarks.urls")),
    path("dropfeed/", include("dropfeed.urls")),
]
```

## Key Files Reference

### Configuration
- `riffs/settings.py` - Django settings with:
  - Security hardening (CSRF, SSL redirect, secure cookies)
  - Constance configuration
  - Static file handling (WhiteNoise)
  - Allowed hosts and trusted origins

### Templates
- `templates/base.html` - Base template with simple.css styling
- `templates/index.html` - Homepage listing public riffs
- Each app has its own templates in `<app>/templates/<app>/`

### Static Files
- `static/simple.min.css` - Minimalist CSS framework for clean styling

### Database
- `db.sqlite3` - SQLite database (not in version control)
- Uses FTS5 extension for full-text search

## Development Guidelines

### Adding a New Riff

1. Create new Django app: `python manage.py startapp <riff_name>`
2. Add app to `INSTALLED_APPS` in `riffs/settings.py`
3. Create models in `<riff_name>/models.py`
4. Create views in `<riff_name>/views.py`
5. Create URL patterns in `<riff_name>/urls.py`
6. Include URLs in `riffs/urls.py`
7. Create templates in `<riff_name>/templates/<riff_name>/`
8. Register models in `<riff_name>/admin.py`
9. Run migrations: `python manage.py makemigrations && python manage.py migrate`

### Adding Full-Text Search

To add FTS5 search to a model:

```python
from django.db import connection

def rebuild_fts_index():
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS myapp_fts")
        cursor.execute("""
            CREATE VIRTUAL TABLE myapp_fts USING fts5(
                field1, field2, content=myapp_mymodel
            )
        """)
        cursor.execute("""
            INSERT INTO myapp_fts(rowid, field1, field2)
            SELECT id, field1, field2 FROM myapp_mymodel
        """)
```

Then in views:
```python
cursor.execute("""
    SELECT m.* FROM myapp_mymodel m
    JOIN myapp_fts f ON m.id = f.rowid
    WHERE myapp_fts MATCH ?
""", [query])
```

### Management Commands

Create in `<app>/management/commands/<command>.py`:
```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Description of command'

    def handle(self, *args, **options):
        # Command logic
        self.stdout.write(self.success('Success message'))
```

Run with: `python manage.py <command>`

### Running the Project

**Development:**
```bash
RIFFS_DEBUG=1 uv run manage.py runserver
```

**Database Migrations:**
```bash
RIFFS_DEBUG=1 uv run manage.py makemigrations
RIFFS_DEBUG=1 uv run manage.py migrate
```

## Testing

When adding tests:

1. Create `tests.py` in each app
2. Use Django's `TestCase` class
3. Run with: `RIFFS_DEBUG uv run manage.py test`

Example test structure:
```python
from django.test import TestCase
from .models import MyModel

class MyModelTestCase(TestCase):
    def test_model_creation(self):
        obj = MyModel.objects.create(name="test")
        self.assertEqual(obj.name, "test")
```

## Security Considerations

### Current Security Features
- CSRF protection enabled
- SSL redirect in production (non-DEBUG mode)
- Secure session cookies
- XFrame options set to DENY
- CSRF trusted origins configured

### Important Security Notes
- **DropFeed URL Path:** The feed path is meant to be secret. Don't expose it publicly.
- **Admin Interface:** Only accessible to authenticated superusers.
- **SQL Injection:** FTS5 queries use parameterized queries. Always use `?` placeholders, never string formatting.

## Deployment

### Static Files

Static files are served via WhiteNoise in production. Run:
```bash
RIFFS_DEBUG=1 uv run manage.py collectstatic
```

## Troubleshooting

### FTS5 Index Issues

If search isn't working:
1. Check if FTS5 table exists: `sqlite3 db.sqlite3 ".tables"`
2. Rebuild index using management command (e.g., `make_bookmarks_fts5_index`)
3. Verify SQLite has FTS5 extension: `sqlite3 db.sqlite3 "PRAGMA compile_options;"`

### Static Files Not Loading

1. Run `python manage.py collectstatic`
2. Check `STATIC_ROOT` and `STATIC_URL` in settings
3. Verify WhiteNoise is in `MIDDLEWARE`

### Migration Issues

If migrations fail:
1. Check database file permissions
2. Delete migration files (except `__init__.py`) and `db.sqlite3`, recreate
3. Run `python manage.py makemigrations` then `python manage.py migrate`

## Common Tasks

### Rebuild Bookmark Search Index
```bash
python manage.py make_bookmarks_fts5_index
```

## Project Philosophy

This project emphasizes:

- **Simplicity:** Clean, minimal design using simple.css
- **Self-hosted:** Run on personal infrastructure
- **Privacy:** No tracking, analytics, or external dependencies
- **Modularity:** Each riff is independent and focused
- **Search:** Full-text search where it matters (bookmarks, quotes)

