from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import include, path

from apps.visualization.api_views import GraphDataView
from todo_project import pwa_views


def home(request):
    return render(request, "home.html")


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "connected"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)


def readiness_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)


def liveness_check(request):
    return JsonResponse({"status": "alive"})


urlpatterns = [
    path("", home, name="home"),
    path("service-worker.js", pwa_views.service_worker, name="service-worker"),
    path("manifest.json", pwa_views.web_manifest, name="web-manifest"),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("health/ready/", readiness_check, name="health-ready"),
    path("health/live/", liveness_check, name="health-live"),
    path("accounts/", include("apps.accounts.urls")),
    path("tasks/", include("apps.tasks.urls")),
    path("visualization/", include("apps.visualization.urls")),
    path("api/graph/data/", GraphDataView.as_view(), name="api-graph-data"),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
