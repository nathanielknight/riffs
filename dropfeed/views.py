import secrets

from constance import config
from constance.models import Constance
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.http.response import FileResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Recording
from .forms import RecordingForm


def _get_or_create_feed_path():
    """
    Retrieves the feed path from constance config.
    If it's empty, generates a new one, saves it, and returns it.
    """
    path = config.DROPFEED_URL_PATH

    # Check if the stored value is empty or looks like a default
    if not path or len(path) < 16:
        new_path = secrets.token_urlsafe(16)
        # Use the Constance API to save it to the database
        Constance.objects.update_or_create(
            key="DROPFEED_URL_PATH", defaults={"value": new_path}
        )
        # Update the in-memory config
        setattr(config, "DROPFEED_URL_PATH", new_path)
        return new_path
    return path


@login_required
def index(request):
    if request.method == "POST":
        form = RecordingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Recording uploaded successfully!")
            return redirect("dropfeed:index")
    else:
        form = RecordingForm()

    recordings = Recording.objects.all()
    total_size = recordings.aggregate(total=Sum("file_size"))["total"] or 0
    total_size_mb = total_size / (1024 * 1024)

    feed_path = _get_or_create_feed_path()
    feed_url = request.build_absolute_uri(
        reverse("dropfeed:feed", kwargs={"path": feed_path})
    )

    context = {
        "form": form,
        "recordings": recordings,
        "total_size_mb": total_size_mb,
        "feed_url": feed_url,
    }
    return render(request, "dropfeed/index.html", context)


def feed(request, path):
    feed_path = _get_or_create_feed_path()
    if path != feed_path:
        return HttpResponse("Not Found", status=404)

    recordings = Recording.objects.all()

    feed_data = {
        "title": config.DROPFEED_TITLE or "My Podcast",
        "description": config.DROPFEED_DESCRIPTION or "A podcast feed",
        "author": config.DROPFEED_AUTHOR or "Podcast Author",
        "link": request.build_absolute_uri("/"),
        "itunes_explicit": "yes" if config.DROPFEED_EXPLICIT else "no",
        "recordings": [],
    }

    for recording in recordings:
        feed_data["recordings"].append(
            {
                "title": recording.name,
                "description": recording.description or recording.name,
                "pub_date": recording.uploaded_at,
                "enclosure_url": request.build_absolute_uri(
                    reverse("dropfeed:recording", kwargs={"id": recording.id})
                ),
                "enclosure_length": recording.file_size,
                "enclosure_type": "audio/mpeg",
            }
        )

    xml_content = render_to_string(
        "dropfeed/feed.xml", {"feed": feed_data}, request=request
    )
    return HttpResponse(xml_content, content_type="application/rss+xml")


def recording(request, id):
    recording = Recording.objects.get(id=id)
    filename = "-".join(recording.name.lower().split()) + ".mp3"
    return FileResponse(recording.audio_file, as_attachment=True, filename=filename)
