from django.contrib import admin
from .models import NewsletterRequest, Newsletter


@admin.register(NewsletterRequest)
class NewsletterRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_by', 'sent_at', 'created_at']
    search_fields = ['subject', 'message']
    readonly_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']