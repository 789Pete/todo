from django.conf import settings
from django.http import HttpResponse


def service_worker(request):
    sw_path = settings.BASE_DIR / "static" / "js" / "service-worker.js"
    with open(sw_path) as f:
        body = f.read()
    response = HttpResponse(body, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def web_manifest(request):
    manifest_path = settings.BASE_DIR / "static" / "manifest.json"
    with open(manifest_path) as f:
        body = f.read()
    return HttpResponse(body, content_type="application/manifest+json")
