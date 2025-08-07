from django.contrib import admin
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from .models import Recording


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ['name', 'uploaded_at', 'file_size_display', 'audio_file_link']
    list_filter = ['uploaded_at']
    search_fields = ['name', 'description']
    readonly_fields = ['file_size', 'uploaded_at']
    
    def file_size_display(self, obj):
        return filesizeformat(obj.file_size)
    file_size_display.short_description = "File Size"
    
    def audio_file_link(self, obj):
        if obj.audio_file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.audio_file.url)
        return "-"
    audio_file_link.short_description = "Audio File"
