from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User
from .permissions import IsSuperUser
from .serializers import UserSerializer, UserStatsSerializer


class SearchUserView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args: object, **kwargs: object) -> QuerySet[User]:
        if "search" in self.request.GET:
            search_query = self.request.GET["search"]
            return User.objects.filter(
                Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
            )
        else:
            return super().get_queryset()


class InstanceUserStats(viewsets.GenericViewSet, generics.ListAPIView):

    queryset = User.objects.all()
    serializer_class = UserStatsSerializer
    permission_classes = [IsSuperUser]

    def get_paginated_response(self, data: list[dict[str, object]]) -> Response:
        return Response(data)

    def get_queryset(self) -> QuerySet[User]:
        data = (
            User.objects.values("id")
            .annotate(created_date=TruncDate("date_joined"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data  # type: ignore[return-value]
