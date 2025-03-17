from django.core.management.base import BaseCommand
from django.db import connection

from bookmarks.models import Bookmark


class Command(BaseCommand):
    help = "Rebuilds the FTS index for existing bookmarks"

    def handle(self, *args, **options):
        self.stdout.write("Starting FTS index rebuild...")

        with connection.cursor() as cursor:
            # First empty the FTS table to avoid duplicates
            self.stdout.write(" ...clearing existing index")
            cursor.execute(
                "INSERT INTO bookmarks_bookmark_fts(bookmarks_bookmark_fts) VALUES('delete')"
            )

            # Get the total count for progress reporting
            bookmark_count = Bookmark.objects.count()
            self.stdout.write(f"  ...found {bookmark_count} bookmarks to index")

            # Bulk-insert directly from the bookmarks table
            self.stdout.write("  ...inserting from bookmarks_bookmark")
            cursor.execute('''
                INSERT INTO bookmarks_bookmark_fts(rowid, name, url, notes)
                SELECT id, 
                        COALESCE(name, ''), 
                        COALESCE(url, ''), 
                        COALESCE(notes, '')
                FROM bookmarks_bookmark
            ''')

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully rebuilt FTS index for {bookmark_count} bookmarks"
            )
        )
