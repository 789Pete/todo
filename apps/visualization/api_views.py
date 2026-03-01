from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.visualization.graph_builder import build_graph_data


class GraphDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_tag = request.query_params.get("filter_tag", "")
        filter_status = request.query_params.get("filter_status", "")
        version_key = f"graph_cache_version_{request.user.id}"
        try:
            version = cache.get(version_key) or 0
        except Exception:
            version = 0
        cache_key = (
            f"graph_data_v{version}_user_{request.user.id}"
            f"_tag_{filter_tag}_status_{filter_status}"
        )
        data = cache.get(cache_key)
        if data is None:
            data = build_graph_data(
                user=request.user,
                filter_tag=filter_tag or None,
                filter_status=filter_status or None,
            )
            cache.set(cache_key, data, 60)  # 60-second TTL
        return Response(data)
