import cuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

def generate_cuid():
    return cuid.cuid()

def resize_image(file, max_width: int, max_height: int):
    img = Image.open(file)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img_format = img.format or "JPEG"
    img.save(buffer, format=img_format, quality=90)
    return ContentFile(buffer.getvalue(), name=file.name)

class BlogPost(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=25,
        default=generate_cuid,  # <--- use wrapper
        editable=False
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to="blog/covers/")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.cover_image and not self.pk:
        # Resize before saving
            self.cover_image = resize_image(self.cover_image, max_width=1200, max_height=800)

        super().save(*args, **kwargs)


    def __str__(self):
        return self.title


# -------------------------------
# Blog comment
# -------------------------------
class BlogComment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# -------------------------------
# Blog Like (unique per user/post)
# -------------------------------
class BlogLike(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
