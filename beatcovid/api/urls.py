from django.urls import include, path
from rest_framework import routers

from .views import FormData, FormSchema, FormStats, FormSubmission

_urls = [
    path("form/schema/<str:form_name>/", FormSchema),
    path("form/stats/<str:form_name>/", FormStats),
    path("form/submit/<str:form_name>/", FormSubmission),
    path("form/data/<str:form_name>/", FormData),
]

# urlpatterns = router.urls += _urls
urlpatterns = _urls
