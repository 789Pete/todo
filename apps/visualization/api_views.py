from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.visualization.graph_builder import build_graph_data


class GraphDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_tag = request.query_params.get("filter_tag")
        filter_status = request.query_params.get("filter_status")
        data = build_graph_data(
            user=request.user,
            filter_tag=filter_tag,
            filter_status=filter_status,
        )
        return Response(data)
