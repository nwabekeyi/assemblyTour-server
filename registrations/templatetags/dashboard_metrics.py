from django import template

from registrations.models import Registration


register = template.Library()


def _safe_count(**filters):
    """Return counts without breaking the admin dashboard if migrations are pending."""
    try:
        return Registration.objects.filter(**filters).count()
    except Exception:
        return 0


@register.simple_tag
def registration_total():
    return _safe_count()


@register.simple_tag
def registration_pending():
    return _safe_count(status="pending")


@register.simple_tag
def registration_completed():
    return _safe_count(status="completed")


@register.simple_tag
def registration_failed():
    return _safe_count(status="failed")
