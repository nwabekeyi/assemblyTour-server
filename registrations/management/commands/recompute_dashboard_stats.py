from django.core.management.base import BaseCommand

from registrations.services import refresh_all_dashboard_stats


class Command(BaseCommand):
    help = "Recompute and persist dashboard stats for every pilgrim"

    def handle(self, *args, **options):
        self.stdout.write("Recomputing dashboard stats...")
        refresh_all_dashboard_stats()
        self.stdout.write(self.style.SUCCESS("Dashboard stats refreshed."))
