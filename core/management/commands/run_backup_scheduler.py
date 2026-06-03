import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the PostgreSQL-to-Google-Drive backup scheduler."

    def add_arguments(self, parser):
        parser.add_argument("--hour", type=int, default=0, help="Hour of day to run the backup, default 0.")
        parser.add_argument("--minute", type=int, default=0, help="Minute of hour to run the backup, default 0.")

    def handle(self, *args, **options):
        timezone = ZoneInfo(settings.TIME_ZONE)
        hour = options["hour"]
        minute = options["minute"]

        self.stdout.write(
            self.style.SUCCESS(
                f"PostgreSQL backup scheduler started. Backups run daily at {hour:02d}:{minute:02d} {settings.TIME_ZONE}."
            )
        )

        while True:
            now = datetime.now(timezone)
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            logger.info("Next PostgreSQL backup scheduled for %s", next_run.isoformat())
            time.sleep(sleep_seconds)

            try:
                call_command("backup_postgres_to_drive")
            except Exception:
                logger.exception("Scheduled PostgreSQL backup failed")
