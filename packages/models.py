from django.db import models

class Package(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price_current = models.DecimalField(max_digits=12, decimal_places=2)
    price_original = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    spiritual_highlights = models.TextField(help_text="Comma-separated spiritual highlights")
    duration_days = models.PositiveIntegerField()
    duration_nights = models.PositiveIntegerField()
    group_size_min = models.PositiveIntegerField(default=20)
    group_size_max = models.PositiveIntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
