from django.urls import include, path
from rest_framework import routers

from .views import FormData, FormSchema, FormStats, FormSubmission

router = routers.DefaultRouter()
# router.register(r"form", FormSchema, basename="form-schema")


_urls = [
    path("form/schema/<str:form_name>/", FormSchema),
    path("form/stats/", FormStats),
    path("form/<str:formid>/submit/", FormSubmission),
    path("form/<str:formid>/data/", FormData),
]

# urlpatterns = router.urls += _urls
urlpatterns = _urls
