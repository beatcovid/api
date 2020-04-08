from django.urls import include, path
from rest_framework import routers

from .views import UserDetailView

router = routers.DefaultRouter()
router.register(r"user", UserDetailView,)

_urls = [
]

urlpatterns = router.urls += _urls
