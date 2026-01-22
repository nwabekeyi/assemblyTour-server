from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image


# -------------------------------
# Image resize helper (Cloudinary-safe)
# -------------------------------
def resize_image(file, max_width: int, max_height: int):
    """
    Resize image using Pillow BEFORE Cloudinary upload.
    Works with InMemoryUploadedFile / UploadedFile.
    """
    img = Image.open(file)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img_format = img.format or "JPEG"
    img.save(buffer, format=img_format, quality=90)

    return ContentFile(buffer.getvalue(), name=file.name)


# ===============================
# HERO SLIDES (Carousel)
# ===============================
class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()

    # Uploads directly to Cloudinary via DEFAULT_FILE_STORAGE
    image = models.ImageField(upload_to="assemblytour/home/hero_slides/")

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.image and not self.pk:
            self.image = resize_image(
                self.image,
                max_width=1920,
                max_height=900
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} - {self.title}"


# ===============================
# EXPERIENCE SECTION (SINGLETON)
# ===============================
class ExperienceSection(models.Model):
    """
    SINGLETON model – only one row allowed
    """
    title = models.CharField(max_length=200)
    body = models.TextField()

    image_one = models.ImageField(upload_to="assemblytour/home/experience/")
    image_two = models.ImageField(upload_to="assemblytour/home/experience/")

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Enforce singleton
        if not self.pk and ExperienceSection.objects.exists():
            raise ValueError("Only one ExperienceSection is allowed")

        if self.image_one and not self.pk:
            self.image_one = resize_image(
                self.image_one,
                max_width=1200,
                max_height=800
            )

        if self.image_two and not self.pk:
            self.image_two = resize_image(
                self.image_two,
                max_width=1200,
                max_height=800
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return "Homepage Experience Section"
