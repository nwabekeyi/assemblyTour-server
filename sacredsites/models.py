from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image


# -------------------------------
# Image resize helper
# -------------------------------
def resize_image(file, max_width: int, max_height: int):
    img = Image.open(file)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img_format = img.format or "JPEG"
    img.save(buffer, format=img_format, quality=90)

    return ContentFile(buffer.getvalue(), name=file.name)


# ===============================
# SACRED SITES
# ===============================
class SacredSite(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()

    # Uploads to Cloudinary automatically
    image = models.ImageField(
        upload_to="assemblytour/sacred_sites/"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Resize only on first upload or when replacing image
        if self.image and not self.pk:
            self.image = resize_image(
                self.image,
                max_width=1600,
                max_height=1000
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
