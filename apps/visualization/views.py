from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GraphView(LoginRequiredMixin, TemplateView):
    template_name = "visualization/graph.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["graph_params"] = self.request.GET
        return context


class SplitView(LoginRequiredMixin, TemplateView):
    template_name = "visualization/split.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["graph_params"] = self.request.GET
        return context
