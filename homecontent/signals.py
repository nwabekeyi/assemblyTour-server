from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import HeroSlide, ExperienceSection


# =====================================================
# DELETE FILES FROM CLOUDINARY WHEN ROW IS DELETED
# =====================================================

@receiver(post_delete, sender=HeroSlide)
def delete_hero_slide_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=ExperienceSection)
def delete_experience_images(sender, instance, **kwargs):
    if instance.image_one:
        instance.image_one.delete(save=False)

    if instance.image_two:
        instance.image_two.delete(save=False)


# =====================================================
# DELETE OLD CLOUDINARY FILE WHEN IMAGE IS UPDATED
# =====================================================

@receiver(pre_save, sender=HeroSlide)
def replace_hero_slide_image(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = HeroSlide.objects.get(pk=instance.pk)
    except HeroSlide.DoesNotExist:
        return

    if old.image and old.image != instance.image:
        old.image.delete(save=False)


@receiver(pre_save, sender=ExperienceSection)
def replace_experience_images(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = ExperienceSection.objects.get(pk=instance.pk)
    except ExperienceSection.DoesNotExist:
        return

    if old.image_one and old.image_one != instance.image_one:
        old.image_one.delete(save=False)

    if old.image_two and old.image_two != instance.image_two:
        old.image_two.delete(save=False)
