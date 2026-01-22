from django.db import models

class HeroSlide(models.Model):
    """
    Each slide in the homepage carousel
    """
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to='home/hero_slides/')
    order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order} - {self.title}"


class ExperienceSection(models.Model):
    """
    The experience section containing two images and a description
    """
    title = models.CharField(max_length=200)
    body = models.TextField()
    image_one = models.ImageField(upload_to='home/experience/')
    image_two = models.ImageField(upload_to='home/experience/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
