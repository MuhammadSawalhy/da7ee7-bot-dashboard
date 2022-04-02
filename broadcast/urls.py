from django.urls import path
from .views import broadcast

urlpatterns = [
    path("/", broadcast)
]
