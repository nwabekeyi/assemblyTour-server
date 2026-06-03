from django.core.management.base import BaseCommand

from core.services.google_drive_backup import backup_postgres_to_google_drive


class Command(BaseCommand):
    help = "Back up the configured PostgreSQL database and replace the backup in Google Drive."

    def handle(self, *args, **options):
        uploaded_file = backup_postgres_to_google_drive()
        self.stdout.write(
            self.style.SUCCESS(
                f"PostgreSQL backup uploaded to Google Drive as {uploaded_file.get('name')} ({uploaded_file.get('id')})."
            )
        )
