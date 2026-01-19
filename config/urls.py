from django.contrib import admin
from django.urls import path, include

API_PREFIX = "api/v1/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path(API_PREFIX, include('accounts.urls')),
    path(API_PREFIX, include('registrations.urls')),
    path(API_PREFIX, include('packages.urls')),
    path(API_PREFIX, include("core.urls")),
    # path(f"{API_PREFIX}blog/", include('blog.urls')),
    # path(f"{API_PREFIX}documents/", include('documents.urls')),
]