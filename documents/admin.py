from django.contrib import admin
from .models import Document, DocumentType

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'upload_by', 'is_active', 'created_at')
    list_filter = ('upload_by', 'is_active')
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'doc_type', 'uploaded_at', 'expiry_date')
    search_fields = ('user__email', 'doc_type__name')
