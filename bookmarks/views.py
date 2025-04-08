from django.db.models import Count
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import django.forms as forms
from taggit.models import Tag

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


def paginated_context(req, bookmarks, context):
    paginator = Paginator(bookmarks, 50)
    page_number = req.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["page"] = page_obj


def bookmark_context(req: HttpRequest):
    context = {}
    if query := req.GET.get("q"):
        bookmarks = Bookmark.objects.raw(
            """
            SELECT bookmarks_bookmark.*
            FROM bookmarks_bookmark
            JOIN bookmarks_bookmark_fts ON bookmarks_bookmark.id = bookmarks_bookmark_fts.rowid
            WHERE bookmarks_bookmark_fts MATCH %s
            ORDER BY rank;
            """,
            [query]
        )
        context["bookmarks"] = bookmarks
        context["search"] = {
            "query": query,
            "resultscount": len(bookmarks),
        }
    else:
        bookmarks = Bookmark.objects.all().order_by("-created_at")
        context["bookmarks"] = bookmarks

    paginator = Paginator(bookmarks, 50)
    page_number = req.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["page"] = page_obj

    new_bookmark_form = NewBookmarkForm()
    context["new_bookmark_form"] = new_bookmark_form

    return context


def get_index(req):
    context = bookmark_context(req)
    return render(req, "bookmarks/index.html", context)


@login_required
def post_new_bookmark(req):
    form = NewBookmarkForm(req.POST)
    form.full_clean()
    if form.is_valid():
        _bookmark = form.save()
        return redirect("bookmarks:index", permanent=False)
    else:
        context = bookmark_context(req)
        context["new_bookmark_form"] = NewBookmarkForm(req.POST)
        return render(req, "bookmarks/index.html", context)


def get_bookmark_details(req, id):
    bookmark = Bookmark.objects.get(id=id)
    context = {
        "bookmark": bookmark
    }
    return render(req, "bookmarks/bookmark.html", context)


def index(req: HttpRequest):
    match req.method:
        case "GET":
            return get_index(req)
        case "POST":
            return post_new_bookmark(req)
        case _:
            return HttpResponseNotAllowed(permitted_methods=["GET", "POST"])


def bookmark(req: HttpRequest, id: int):
    match req.method:
        case "GET":
            return get_bookmark_details(req, id)
        case _:
            return HttpResponseNotAllowed(permitted_methods=["GET"])


def tag_index(req):
    tags = (
        Tag.objects.annotate(count=Count("taggit_taggeditem_items"))
        .order_by("-count")
        .all()
    )
    return render(req, "bookmarks/tags.html", {"tags": tags})


def tag_detail(req, tagid):
    tag = Tag.objects.get(pk=tagid)
    bookmarks = (
        Bookmark.objects.filter(tags__name=tag.name).order_by("-created_at").all()
    )
    count = bookmarks.count()
    return render(
        req, "bookmarks/tag.html", {"tag": tag, "bookmarks": bookmarks, "count": count}
    )
