from django.db import models
from django.conf import settings
import cuid

def generate_cuid():
    return cuid.cuid()

class DocumentType(models.Model):
    UPLOAD_BY_CHOICES = [
        ('user', 'User Only'),
        ('admin', 'Admin Only'),
        ('both', 'User and Admin'),
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    upload_by = models.CharField(max_length=10, choices=UPLOAD_BY_CHOICES, default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    id = models.CharField(max_length=25, primary_key=True, default=generate_cuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name='documents')
    file_url = models.URLField(
        default="https://res.cloudinary.com/your_cloud_name/raw/upload/assembly-tour/placeholders/document-placeholder.pdf"
    )
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.email} - {self.doc_type.name}"
