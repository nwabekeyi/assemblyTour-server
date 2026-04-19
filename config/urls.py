from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect

API_PREFIX = "api/v1/"

admin.site.login_url = "/admin/login/"


class StaffRequiredAdminSite(admin.AdminSite):
    def login(self, request, extra_context=None):
        # Use default login first, then check staff status after auth
        return super().login(request, extra_context)

    def admin_view(self, request, extra_context=None):
        if request.user.is_authenticated and not request.user.is_staff:
            return HttpResponseRedirect('/admin/login/?next=/admin/')
        return super().admin_view(request, extra_context)


admin.site.login = LoginView.as_view(
    template_name='admin/login.html',
    redirect_authenticated_user=True,
)


def staff_required_login(request, **kwargs):
    """Custom login view that checks for staff status."""
    if request.user.is_authenticated and request.user.is_staff:
        return HttpResponseRedirect('/admin/')
    return LoginView.as_view(
        template_name='admin/login.html',
        redirect_authenticated_user=True,
    )(request, **kwargs)


urlpatterns = [
    path('admin/login/', staff_required_login, name='admin_login'),
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