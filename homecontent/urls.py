from django.urls import path
from .views import HomeContentView

urlpatterns = [
    path("home-content/", HomeContentView.as_view(), name="home-content"),
]
