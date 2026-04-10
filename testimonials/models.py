from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Testimonial(models.Model):
    author_name = models.CharField(max_length=100)
    author_image = models.URLField(max_length=500, blank=True, null=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Testimonial by {self.author_name}"