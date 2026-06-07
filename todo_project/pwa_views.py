from django.conf import settings
from django.http import Http404, HttpResponse


def service_worker(request):
    sw_path = settings.BASE_DIR / "static" / "js" / "service-worker.js"
    try:
        with open(sw_path, encoding="utf-8") as f:
            body = f.read()
    except OSError:
        raise Http404("service-worker.js not found")
    response = HttpResponse(body, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def web_manifest(request):
    manifest_path = settings.BASE_DIR / "static" / "manifest.json"
    try:
        with open(manifest_path, encoding="utf-8") as f:
            body = f.read()
    except OSError:
        raise Http404("manifest.json not found")
    return HttpResponse(body, content_type="application/manifest+json")
