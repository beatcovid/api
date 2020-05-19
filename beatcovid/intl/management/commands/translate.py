import logging

from django.core.management.base import BaseCommand, CommandError

from beatcovid.core.lokalise import Lokalise
from beatcovid.intl.controllers import extract_messages, update_keys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Uploads and updates keys to lokalise"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Don't save new translations",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        l = Lokalise()

        messages = extract_messages()

        keys = update_keys(l, messages)
