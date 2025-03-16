from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseNotAllowed
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import django.forms as forms

from .models import Bookmark

"""
Endpoints:

- GET / index page
- POST / new bookmark
- GET /:id item detail
- GET /tags tag index
- GET /tags/:id tagdetail
"""


class NewBookmarkForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        fields = ["name", "url", "notes", "tags"]


def get_index(req):
    bookmarks = Bookmark.objects.all()
    paginator = Paginator(bookmarks, 50)
    page_number = req.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(req, "bookmarks/index.html", {"bookmarks_page": page_obj})


def post_new_bookmark(req):
    raise Exception("unimp")


def get_bookmark_details(req, id):
    raise Exception("unimp")


@login_required
def index(req: HttpRequest):
    match req.method:
        case "GET":
            return get_index(req)
        case "POST":
            return post_new_bookmark(req)
        case _:
            return HttpResponseNotAllowed(permitted_methods=["GET", "POST"])


@login_required
def bookmark(req: HttpRequest, id: int):
    match req.method:
        case "GET": 
            return get_bookmark_details(req, id)
        case _:
            return HttpResponseNotAllowed(permitted_methods=["GET"])
