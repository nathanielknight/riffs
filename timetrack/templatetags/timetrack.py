from django import template
from django.utils.html import format_html

register = template.Library()


def hm(seconds):
    minutes = int(seconds) // 60
    return f"{minutes // 60}:{minutes % 60:02d}"


@register.simple_tag
def duration(value, live=False):
    """Render a timedelta as h:mm; live durations tick forward in the page."""
    seconds = int(value.total_seconds())
    return format_html(
        '<span class="duration"{} data-seconds="{}">{}</span>',
        " data-live" if live else "",
        seconds,
        hm(seconds),
    )


@register.simple_tag
def total(value):
    return duration(value.duration, value.live)
