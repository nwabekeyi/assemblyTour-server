from django.urls import path
from .views import LivenessView

urlpatterns = [
    path("health/", LivenessView.as_view(), name="health"),
]
