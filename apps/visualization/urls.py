from django.urls import path

from apps.visualization.views import GraphView

urlpatterns = [
    path("", GraphView.as_view(), name="graph-view"),
]
