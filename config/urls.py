from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

API_PREFIX = "api/v1/"

urlpatterns = [
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    path(API_PREFIX, include('accounts.urls')),
    path(API_PREFIX, include('registrations.urls')),
    path(API_PREFIX, include('payments.urls')),
    path(API_PREFIX, include('packages.urls')),
    path(API_PREFIX, include("core.urls")),
    path(API_PREFIX, include("homecontent.urls")),
    path(API_PREFIX, include('blog.urls')),
    path(API_PREFIX, include('faqs.urls')),
    path(f"{API_PREFIX}documents/", include('documents.urls')),
    path(API_PREFIX, include("sacredsites.urls")),
    path(API_PREFIX, include("newsletter.urls")),

]