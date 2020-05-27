import logging

from django.core.management.base import BaseCommand, CommandError

from beatcovid.symtracker.exporter import export_test

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Exports symtracker test cases as spreadhseet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Don't save output file",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        export_test()
