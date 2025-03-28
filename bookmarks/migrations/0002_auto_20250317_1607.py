# Generated by Django 5.1.7 on 2025-03-17 16:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bookmarks", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Create the FTS5 table to index the main table
            CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_bookmark_fts USING fts5(
                name, 
                url, 
                notes, 
                content='bookmarks_bookmark', 
                content_rowid='id'
            );

            -- Create a trigger to update the FTS table on INSERT
            CREATE TRIGGER IF NOT EXISTS bookmarks_bookmark_ai AFTER INSERT ON bookmarks_bookmark
            BEGIN
                INSERT INTO bookmarks_bookmark_fts(rowid, name, url, notes)
                VALUES (new.id, new.name, new.url, new.notes);
            END;

            -- Create a trigger to update the FTS table on UPDATE
            CREATE TRIGGER IF NOT EXISTS bookmarks_bookmark_au AFTER UPDATE ON bookmarks_bookmark
            BEGIN
                INSERT INTO bookmarks_bookmark_fts(bookmarks_bookmark_fts, rowid, name, url, notes)
                VALUES ('delete', old.id, old.name, old.url, old.notes);
                
                INSERT INTO bookmarks_bookmark_fts(rowid, name, url, notes)
                VALUES (new.id, new.name, new.url, new.notes);
            END;

            -- Create a trigger to update the FTS table on DELETE
            CREATE TRIGGER IF NOT EXISTS bookmarks_bookmark_ad AFTER DELETE ON bookmarks_bookmark
            BEGIN
                INSERT INTO bookmarks_bookmark_fts(bookmarks_bookmark_fts, rowid, name, url, notes)
                VALUES ('delete', old.id, old.name, old.url, old.notes);
            END;
            """,
            reverse_sql="""
            -- Drop triggers first
            DROP TRIGGER IF EXISTS bookmarks_bookmark_ai;
            DROP TRIGGER IF EXISTS bookmarks_bookmark_au;
            DROP TRIGGER IF EXISTS bookmarks_bookmark_ad;
            
            -- Then drop the FTS table
            DROP TABLE IF EXISTS bookmarks_bookmark_fts;
        """,
        )
    ]
