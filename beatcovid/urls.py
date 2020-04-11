from django.contrib import admin
from django.urls import include, path

from beatcovid.api.views import FormData, FormSchema, FormStats, FormSubmission
from beatcovid.respondent.views import UserDetailView

admin.site.site_header = "beatcovid19 Admin"
admin.site.site_title = "beatcovid19 Admin"
admin.site.index_title = "beatcovid19 Admin"

urlpatterns = [
    path("api/", include("beatcovid.api.urls")),
    path("api/form/schema/<str:form_name>/", FormSchema),
    path("api/form/stats/<str:form_name>/", FormStats),
    path("api/form/submit/<str:form_name>/", FormSubmission),
    path("api/form/data/<str:form_name>/", FormData),
    path("user", UserDetailView.as_view()),
    # path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("admin/", admin.site.urls),
]
