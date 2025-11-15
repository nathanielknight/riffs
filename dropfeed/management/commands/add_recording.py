import pathlib
import typing
from django.core.files import File
from django.core.management.base import BaseCommand, CommandParser

from dropfeed.models import Recording

if typing.TYPE_CHECKING:
    import argparse


class Command(BaseCommand):
    help = "Add audio recording files from the CLI"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "files",
            nargs="+",
            type=pathlib.Path,
            help="Path(s) to audio file(s) to add",
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Name for the recording (defaults to filename without extension)",
        )
        parser.add_argument(
            "--description",
            type=str,
            default="",
            help="Description for the recording",
        )

    def handle(self, *args: typing.Any, **options: typing.Any) -> None:
        files = options["files"]
        name = options.get("name")
        description = options.get("description", "")

        if len(files) > 1 and name:
            self.stderr.write(
                self.style.ERROR(
                    "Cannot specify --name when adding multiple files. "
                    "Use one file at a time with --name, or omit --name to use filenames."
                )
            )
            return

        for file_path in files:
            if not isinstance(file_path, pathlib.Path):
                file_path = pathlib.Path(file_path)

            if not file_path.exists():
                self.stderr.write(
                    self.style.ERROR(f"File does not exist: {file_path}")
                )
                continue

            if not file_path.is_file():
                self.stderr.write(
                    self.style.ERROR(f"Not a file: {file_path}")
                )
                continue

            # Use provided name or derive from filename
            recording_name = name if name else file_path.stem

            try:
                # Open the file and create the Recording
                with open(file_path, "rb") as f:
                    django_file = File(f, name=file_path.name)
                    recording = Recording(
                        name=recording_name,
                        description=description,
                    )
                    recording.audio_file.save(file_path.name, django_file, save=True)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully added recording '{recording.name}' "
                        f"(ID: {recording.id}) from {file_path}"
                    )
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to add recording from {file_path}: {str(e)}"
                    )
                )
