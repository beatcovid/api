from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "beatcovid19 Admin"
admin.site.site_title = "beatcovid19 Admin"
admin.site.index_title = "beatcovid19 Admin"

urlpatterns = [
    path("api/", include("beatcovid.api.urls")),
    path("user/", include("beatcovid.respondent.urls")),
    # path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("admin/", admin.site.urls),
]
