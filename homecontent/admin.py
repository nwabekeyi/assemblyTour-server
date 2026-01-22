from django.contrib import admin
from .models import HeroSlide, ExperienceSection

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['title']
    ordering = ['order']


@admin.register(ExperienceSection)
class ExperienceSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']
    list_editable = ['is_active']
    list_display_links = ['title']
