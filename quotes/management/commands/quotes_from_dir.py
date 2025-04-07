import datetime
import logging
import pathlib
import typing

from django.core.management.base import BaseCommand

from quotes.models import Quote

if typing.TYPE_CHECKING:
    import argparse


LEAD_CHAR = "$"


def parse_leadline(line: str, log) -> typing.Tuple[str, str]:
    log.debug("parsing lead line: {}".format(line))
    assert line.startswith(LEAD_CHAR)
    line = line.lstrip(LEAD_CHAR).strip()
    key, value = line.split(":", 1)
    key = key.strip()
    value = value.strip()
    log.debug("parsed: key='{}', value='{}'".format(key, value))
    assert key in ["slug", "source", "link"], "Invalid lead line: {}".format(line)
    assert value, "Empty lead: {}".format(line)
    return key, value


def parse_entry(srcpath: pathlib.Path, log) -> typing.Tuple[Quote, datetime.datetime]:
    src = srcpath.read_text()
    ctime = srcpath.stat().st_ctime
    mtime = srcpath.stat().st_mtime

    leadlines: typing.List[str] = []
    bodylines: typing.List[str] = []
    for line in src.splitlines():
        if line.startswith(LEAD_CHAR):
            leadlines.append(line)
        else:
            bodylines.append(line)
    leads = {k: v for k, v in map(lambda l: parse_leadline(l, log), leadlines)}
    assert "slug" in leads, "Missing 'slug' leader"
    assert "source" in leads, "Missing 'source' leader"
    body = "\n".join(bodylines).strip()
    assert body, "Empty body"
    return (
        Quote(
            slug=leads["slug"],
            source=leads["source"],
            content=body.strip(),
            link=leads.get("link"),
            created_at=mtime,
            updated_at=ctime,
        ),
        datetime.datetime.fromtimestamp(mtime),
    )


class Command(BaseCommand):
    help = "Import quotes from a directory of text files"

    def add_arguments(self, parser: "argparse.ArgumentParser") -> None:
        parser.add_argument("directory", type=pathlib.Path)

    def handle(self, *args: typing.Any, **options: typing.Any) -> None:
        log = logging.getLogger(__name__)
        directory = options["directory"]
        if not isinstance(directory, pathlib.Path):
            raise TypeError("directory must be a pathlib.Path")
        if not directory.exists():
            raise FileNotFoundError(f"directory {directory} does not exist")
        if not directory.is_dir():
            raise NotADirectoryError(f"directory {directory} is not a directory")

        quotes = []
        for src in directory.iterdir():
            if src.is_file():
                quote = parse_entry(src, log)
                quotes.append(quote)

        for (quote, ctime) in quotes:
            quote.save()
            quote.created_at = ctime
            quote.save()
