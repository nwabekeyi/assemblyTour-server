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
# PACKAGE MODEL
# ===============================
class Package(models.Model):
    CATEGORY_CHOICES = (
        ("umrah", "Umrah"),
        ("hajj", "Hajj"),
    )

    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    # Cover image (Cloudinary)
    cover_image = models.ImageField(
        upload_to="assemblytour/packages/covers/"
    )

    price_current = models.DecimalField(max_digits=12, decimal_places=2)
    price_original = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    description = models.TextField()
    type = models.CharField(
        max_length=150,
        blank=True,
        help_text="Short description of the package"
    )
    spiritual_highlights = models.TextField(
        help_text="Comma-separated spiritual highlights"
    )

    duration_days = models.PositiveIntegerField()
    duration_nights = models.PositiveIntegerField()

    group_size_min = models.PositiveIntegerField(default=20)
    group_size_max = models.PositiveIntegerField(default=40)

    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default="umrah",
        help_text="Category of the package (Umrah or Hajj)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Resize only on first upload
        if self.cover_image and not self.pk:
            self.cover_image = resize_image(
                self.cover_image,
                max_width=1200,
                max_height=800
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
