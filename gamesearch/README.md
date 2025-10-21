# Game Search App

A Django app providing faceted search functionality over a games SQLite database.

## Features

- **Text Search**: Search by game title and author name
- **Tag Filtering**: Select from available tags to filter games
- **Starred Games**: Filter to show only starred games
- **Combined Filters**: Use multiple filters simultaneously

## Database Schema

The app connects to an external SQLite database (`games.db`) with the following schema:

```sql
CREATE TABLE rawgames (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   title TEXT,
   authors TEXT,
   tags TEXT,
   path TEXT
);

CREATE TABLE stars (
    gameid INTEGER NOT NULL UNIQUE
);
```

**Note**: The `id` column is required for Django ORM compatibility. Tags should be stored as comma-separated values in the `tags` field.

## Configuration

The app is configured to use a separate database connection named `games`:

- Database file: `games.db` (located in project root)
- Database router: `gamesearch.routers.GamesRouter`
- Models are unmanaged (`managed = False`) as the database is generated externally

## URL Structure

- `/games/` - Main search interface

## Usage

1. Navigate to `/games/` to access the search interface
2. Use the search filters:
   - **Title**: Enter partial or full game title
   - **Authors**: Enter partial or full author name
   - **Tags**: Select one or more tags (use Ctrl/Cmd for multiple selection)
   - **Starred**: Check to show only starred games
3. Click "Search" to apply filters
4. Click "Clear Filters" to reset the search

## Implementation Notes

- Uses server-side templating (no JavaScript required)
- Brute-force tag collection is used, suitable for databases with a few thousand entries
- Text searches are case-insensitive
- Multiple tag selection uses OR logic (games matching any selected tag are shown)
