from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("I AM ON!", content_type="text/plain")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("", health_check), 
]
