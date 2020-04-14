from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from beatcovid.api.views import (
    FormData,
    FormSchema,
    FormStats,
    FormSubmission,
    SymptomTracker,
)
from beatcovid.respondent.views import UserDetailView

admin.site.site_header = "beatcovid19 Admin"
admin.site.site_title = "beatcovid19 Admin"
admin.site.index_title = "beatcovid19 Admin"

urlpatterns = [
    path("api/form/schema/<str:form_name>/", FormSchema),
    path("api/form/stats/<str:form_name>/", FormStats),
    path("api/form/submit/<str:form_name>/", FormSubmission),
    path("api/form/data/<str:form_name>/", FormData),
    path("api/tracker/", SymptomTracker),
    path("api/user/", UserDetailView),
    path("admin/", admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
