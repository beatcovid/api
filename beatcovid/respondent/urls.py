from django.urls import include, path
from rest_framework import routers

from .views import UserDetailView

urlpatterns = [path("user", UserDetailView.as_view())]
