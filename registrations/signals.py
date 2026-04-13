from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from .models import (
    Registration,
    TravelDocument,
)
from .services import refresh_user_dashboard_stats, complete_travel_documents_step


@receiver(post_save, sender=Registration)
def update_stats_on_save(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)


@receiver(post_delete, sender=Registration)
def update_stats_on_delete(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)


@receiver(post_save, sender=TravelDocument)
def check_travel_documents_complete(sender, instance, created, **kwargs):
    if not created:
        return
    
    registration = instance.registration
    doc_count = registration.travel_documents.count()
    
    if doc_count == 3:
        print(f"SIGNAL: 3 documents for registration {registration.id}. Completing step.")
        try:
            complete_travel_documents_step(registration)
        except Exception as e:
            print(f"SIGNAL ERROR: {e}")
