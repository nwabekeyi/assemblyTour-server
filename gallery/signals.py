from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Gallery


@receiver(post_delete, sender=Gallery)
def delete_gallery_files(sender, instance, **kwargs):
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)

    if instance.media:
        instance.media.delete(save=False)


@receiver(pre_save, sender=Gallery)
def replace_gallery_files(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = Gallery.objects.get(pk=instance.pk)
    except Gallery.DoesNotExist:
        return

    if old.thumbnail and old.thumbnail != instance.thumbnail:
        old.thumbnail.delete(save=False)

    if old.media and old.media != instance.media:
        old.media.delete(save=False)
