from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image


def resize_image(file, max_width: int, max_height: int):
    img = Image.open(file)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img_format = img.format or "JPEG"
    img.save(buffer, format=img_format, quality=90)
    return ContentFile(buffer.getvalue(), name=file.name)


class Gallery(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        YOUTUBE = "youtube", "YouTube"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    url = models.URLField(max_length=1000, blank=True)
    thumbnail = models.ImageField(upload_to="assemblytour/gallery/thumbnails/", blank=True, null=True)
    thumbnail_public_id = models.CharField(max_length=255, blank=True, null=True)
    media = models.ImageField(upload_to="assemblytour/gallery/media/", blank=True, null=True)
    media_public_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]
        verbose_name = "Gallery item"
        verbose_name_plural = "Gallery items"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "gallery-item"
            slug = base_slug
            counter = 1
            while Gallery.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug

        if self.thumbnail and not self.pk:
            self.thumbnail = resize_image(self.thumbnail, max_width=800, max_height=600)

        if self.media and not self.pk:
            self.media = resize_image(self.media, max_width=1920, max_height=1080)

        super().save(*args, **kwargs)
