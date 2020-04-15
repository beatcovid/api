from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from beatcovid.api.views import (
    FormData,
    FormSchema,
    FormStats,
    FormSubmission,
    UserSubmissionView,
)
from beatcovid.respondent.views import GetUID, TransferRequest, UserDetailView
from beatcovid.symtracker.views import SymptomTracker

admin.site.site_header = "beatcovid19 Admin"
admin.site.site_title = "beatcovid19 Admin"
admin.site.index_title = "beatcovid19 Admin"

favicon_view = RedirectView.as_view(url="/staticfiles/favicon.ico", permanent=True)

urlpatterns = [
    path("api/form/schema/<str:form_name>/", FormSchema),
    path("api/form/stats/<str:form_name>/", FormStats),
    path("api/form/submit/<str:form_name>/", FormSubmission),
    path("api/form/data/<str:form_name>/", FormData),
    path("api/tracker/", SymptomTracker),
    path("api/user/submissions/<str:form_name>/", UserSubmissionView),
    path("api/user/submissions/", UserSubmissionView),
    path("api/user/", UserDetailView),
    path("api/transfer/request/", TransferRequest.as_view()),
    path("api/transfer/getUID/", GetUID.as_view()),
    path("admin/", admin.site.urls),
    path("favicon.ico", favicon_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
