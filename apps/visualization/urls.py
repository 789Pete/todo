from django.urls import path

from apps.visualization.views import GraphView, SplitView

urlpatterns = [
    path("", GraphView.as_view(), name="graph-view"),
    path("split/", SplitView.as_view(), name="split-view"),
]
