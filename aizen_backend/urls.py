from django.contrib import admin
from django.urls import path, include

def health_check(request):
    return HttpResponse("OK", content_type="text/plain")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("/", health_check), 
]
