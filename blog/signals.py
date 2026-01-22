from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import BlogPost

# DELETE CLOUDINARY IMAGE ON POST DELETE
@receiver(post_delete, sender=BlogPost)
def delete_blog_cover_image(sender, instance, **kwargs):
    if instance.cover_image:
        instance.cover_image.delete(save=False)

# DELETE OLD CLOUDINARY IMAGE ON UPDATE
@receiver(pre_save, sender=BlogPost)
def replace_blog_cover_image(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = BlogPost.objects.get(pk=instance.pk)
    except BlogPost.DoesNotExist:
        return

    if old.cover_image and old.cover_image != instance.cover_image:
        old.cover_image.delete(save=False)
