from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import SacredSite


# =====================================================
# DELETE CLOUDINARY IMAGE WHEN ROW IS DELETED
# =====================================================
@receiver(post_delete, sender=SacredSite)
def delete_sacred_site_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


# =====================================================
# DELETE OLD CLOUDINARY IMAGE WHEN IMAGE IS UPDATED
# =====================================================
@receiver(pre_save, sender=SacredSite)
def replace_sacred_site_image(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = SacredSite.objects.get(pk=instance.pk)
    except SacredSite.DoesNotExist:
        return

    if old.image and old.image != instance.image:
        old.image.delete(save=False)
