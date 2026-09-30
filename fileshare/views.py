from django.http import FileResponse, Http404, HttpResponse
from .models import ShareFile


def serve_file(request, share_key):
    """
    Serve a file by its share key if it's not expired.

    Args:
        request: The HTTP request
        share_key: The UUID share key for the file

    Returns:
        FileResponse with the file or 404/403 error
    """
    try:
        sharefile = ShareFile.objects.get(share_key=share_key)
    except ShareFile.DoesNotExist:
        return HttpResponse("File not found", status=404)

    if sharefile.is_expired():
        return HttpResponse("This file has expired and is no longer available.", status=403)

    try:
        response = FileResponse(sharefile.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{sharefile.file.name.split("/")[-1]}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found on server")
