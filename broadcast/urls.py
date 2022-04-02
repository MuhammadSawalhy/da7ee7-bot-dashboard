
from django.urls import path
from . import views

urlpatterns = [
    path("", views.broadcast_page, name="broadcast"),
    path("message/", views.broadcast, name="broadcast_POST")
]
