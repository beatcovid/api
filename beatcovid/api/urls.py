from django.urls import include, path
from rest_framework import routers

from .views import FormSchema

router = routers.DefaultRouter()
# router.register(r"form", FormSchema, basename="form-schema")


_urls = [
    path("form/schema/<str:form_name>/", FormSchema),
]

# urlpatterns = router.urls += _urls
urlpatterns = _urls
