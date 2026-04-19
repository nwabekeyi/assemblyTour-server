from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

API_PREFIX = "api/v1/"

admin.site.login_url = "/admin/login/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin/login/', permanent=False)),
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
    path(API_PREFIX, include("testimonials.urls")),
    path(f"{API_PREFIX}contact/", include("contact.urls")),
]