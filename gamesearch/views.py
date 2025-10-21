from django.shortcuts import render
from django.db.models import Q
from urllib.parse import urlencode
from .models import RawGame, Star


def search_games(request):
    """
    Faceted search view for games.
    Supports filtering by:
    - title (text search)
    - authors (text search)
    - tags (select from list)
    - starred status
    """
    # Get filter parameters
    title_query = request.GET.get("title", "").strip()
    author_query = request.GET.get("authors", "").strip()
    selected_tags = request.GET.getlist("tags")
    show_starred = request.GET.get("starred", "")

    # Start with all games
    games = RawGame.objects.using("games").all()

    # Apply title filter
    if title_query:
        games = games.filter(title__icontains=title_query)

    # Apply author filter
    if author_query:
        games = games.filter(authors__icontains=author_query)

    # Apply tag filter
    if selected_tags:
        # Filter games that contain any of the selected tags
        tag_filter = Q()
        for tag in selected_tags:
            tag_filter |= Q(tags__icontains=tag)
        games = games.filter(tag_filter)

    # Apply starred filter
    if show_starred:
        starred_ids = Star.objects.using("games").values_list("gameid", flat=True)
        games = games.filter(id__in=starred_ids)

    # Get all unique tags for the faceted search
    # Note: This uses a brute-force approach, iterating through all games
    # to extract unique tags. This is acceptable for databases with a few
    # thousand entries as specified in requirements.
    tag_counts = {}
    for game in RawGame.objects.using("games").all():
        if game.tags:
            tags = [tag.strip() for tag in game.tags.split(",") if tag.strip()]
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    all_tags = sorted(tag_counts.keys())

    # Get starred game IDs for display
    starred_ids = set(Star.objects.using("games").values_list("gameid", flat=True))

    # Build helper data for tag links
    def build_tag_url(tag, action="add"):
        """Build URL with tag added or removed"""
        params = []
        if title_query:
            params.append(("title", title_query))
        if author_query:
            params.append(("authors", author_query))
        if show_starred:
            params.append(("starred", "1"))

        if action == "add":
            # Add all selected tags plus the new one
            for t in selected_tags:
                params.append(("tags", t))
            params.append(("tags", tag))
        else:  # remove
            # Add all selected tags except the one to remove
            for t in selected_tags:
                if t != tag:
                    params.append(("tags", t))

        return "?" + urlencode(params) if params else "?"

    # Build lists of (tag, url, count) tuples for template
    available_tags = [(tag, build_tag_url(tag, "add"), tag_counts.get(tag, 0)) for tag in all_tags if tag not in selected_tags]
    selected_tag_links = [(tag, build_tag_url(tag, "remove"), tag_counts.get(tag, 0)) for tag in selected_tags]

    context = {
        "games": games,
        "available_tags": available_tags,
        "selected_tag_links": selected_tag_links,
        "title_query": title_query,
        "author_query": author_query,
        "show_starred": show_starred,
        "starred_ids": starred_ids,
        "total_count": games.count(),
    }

    return render(request, "gamesearch/search.html", context)
