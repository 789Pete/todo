from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GraphView(LoginRequiredMixin, TemplateView):
    template_name = "visualization/graph.html"
