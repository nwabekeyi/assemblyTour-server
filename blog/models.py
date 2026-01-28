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


# ────────────────────────────────────────────────
# BLOG POST
# ────────────────────────────────────────────────
class BlogPost(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=25,
        default=generate_cuid,
        editable=False
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()

    cover_image = models.ImageField(upload_to="blog/covers/")

    author_name = models.CharField(max_length=100)
    author_image = models.ImageField(
        upload_to="blog/authors/",
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_blog_posts"
    )

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)

    read_time = models.PositiveIntegerField(
        default=5,
        help_text="Minimum estimated read time for this blog in minutes"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.cover_image and not self.pk:
            self.cover_image = resize_image(
                self.cover_image,
                max_width=1200,
                max_height=800
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# ────────────────────────────────────────────────
# BLOG COMMENT
# ────────────────────────────────────────────────
class BlogComment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: for nested/threaded comments in the future
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_comments"          # ← changed: no clash
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"


# ────────────────────────────────────────────────
# BLOG REPLY (separate flat model)
# ────────────────────────────────────────────────
class BlogReply(models.Model):
    comment = models.ForeignKey(
        BlogComment,
        on_delete=models.CASCADE,
        related_name="flat_replies"            # ← changed: no clash with child_comments
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_replies"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Blog Reply"
        verbose_name_plural = "Blog Replies"

    def __str__(self):
        return f"Reply by {self.user} to comment {self.comment_id}"


# ────────────────────────────────────────────────
# BLOG LIKE
# ────────────────────────────────────────────────
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
        ordering = ["-created_at"]


# ────────────────────────────────────────────────
# BLOG VIEWER
# ────────────────────────────────────────────────
class BlogViewer(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="viewers"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="For anonymous users, track via session or cookie"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user", "session_id")
        ordering = ["-viewed_at"]

    def __str__(self):
        if self.user:
            return f"{self.user} viewed {self.post}"
        return f"Anonymous ({self.session_id}) viewed {self.post}"