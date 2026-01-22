from django.urls import path
from .views import SacredSiteListView

urlpatterns = [
    path("sacred-sites/", SacredSiteListView.as_view(), name="sacred-sites"),
]
