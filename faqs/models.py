from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255, help_text="The question or heading of the FAQ")
    answer = models.TextField(help_text="The answer or content of the FAQ")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question
