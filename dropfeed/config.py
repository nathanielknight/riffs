CONSTANCE_CONFIG = {
    'DROPFEED_TITLE': ('My Podcast', 'Podcast title shown in RSS feed'),
    'DROPFEED_DESCRIPTION': ('A podcast feed', 'Podcast description shown in RSS feed'),
    'DROPFEED_AUTHOR': ('Podcast Author', 'Podcast author shown in RSS feed'),
    'DROPFEED_URL_PATH': ('', 'URL path for RSS feed (automatically generated if empty)'),
    'DROPFEED_ITUNES_CATEGORY': ('Technology', 'iTunes category for the podcast'),
    'DROPFEED_EXPLICIT': (False, 'Whether the podcast contains explicit content'),
}

CONSTANCE_CONFIG_FIELDSETS = {
    'DropFeed Podcast Settings': {
        'fields': (
            'DROPFEED_TITLE',
            'DROPFEED_DESCRIPTION', 
            'DROPFEED_AUTHOR',
            'DROPFEED_URL_PATH',
            'DROPFEED_ITUNES_CATEGORY',
            'DROPFEED_EXPLICIT',
        ),
        'collapse': False,
    },
}