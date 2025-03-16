import os
import sqlite3
from django.core.management.base import BaseCommand, CommandError
from bookmarks.models import Bookmark
from django.utils.dateparse import parse_datetime
import datetime

class Command(BaseCommand):
    help = 'Import bookmarks from a SQLite database file'

    def add_arguments(self, parser):
        parser.add_argument('db_path', type=str, help='Path to the SQLite database file')
        
    def handle(self, *args, **options):
        db_path = options['db_path']
        
        if not os.path.exists(db_path):
            raise CommandError(f"Database file not found at {db_path}")
            
        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            
            # Query to get bookmarks with their tags and modified date
            query = """
            SELECT b.id, b.url, b.title, b.modified, GROUP_CONCAT(t.name, ',') as tags
            FROM bookmark b
            LEFT JOIN bookmark_tag bt ON b.id = bt.bookmark_id
            LEFT JOIN tag t ON bt.tag_id = t.id
            GROUP BY b.id
            """
            
            cursor.execute(query)
            bookmarks_data = cursor.fetchall()
            
            count = 0
            # Import and save bookmarks
            for bookmark_id, url, title, modified_date, tags_string in bookmarks_data:
                # Parse the modified date
                try:
                    # Try to parse the timestamp from SQLite
                    if modified_date:
                        # Handle different timestamp formats
                        if 'T' in modified_date:
                            # ISO format
                            created_at = parse_datetime(modified_date)
                        else:
                            # SQLite default format (YYYY-MM-DD HH:MM:SS)
                            created_at = datetime.datetime.strptime(
                                modified_date, '%Y-%m-%d %H:%M:%S'
                            )
                    else:
                        created_at = None
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(
                        f"Could not parse date '{modified_date}' for bookmark '{title}', using current time."
                    ))
                    created_at = None
                
                # Create a new bookmark using the Django model
                bookmark = Bookmark(
                    name=title,
                    url=url,
                )
                
                # If we have a valid timestamp, set it
                if created_at:
                    bookmark.created_at = created_at
                    bookmark.updated_at = created_at  # Set updated_at to the same value initially
                
                # Save with the specified dates
                bookmark.save()
                
                # Add tags if they exist
                if tags_string:
                    tag_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                    bookmark.tags.add(*tag_list)
                
                count += 1
                
                # Show progress
                if count % 10 == 0:
                    self.stdout.write(f"Imported {count} bookmarks...")
            
            connection.close()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} bookmarks'))
            
        except Exception as e:
            raise CommandError(f"Error importing bookmarks: {e}")