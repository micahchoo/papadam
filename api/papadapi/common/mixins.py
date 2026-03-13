from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework.response import Response

from papadapi.common.functions import create_or_update_tag, recalculate_tag_count
from papadapi.common.models import Tags

if TYPE_CHECKING:
    from rest_framework.request import Request


class TagAddMixin:
    """Mixin for adding tags to a model instance.

    Expects the viewset to define queryset, serializer_class, etc.
    The model instance must have a ``.tags`` M2M field.
    """

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        m = self.get_object()  # type: ignore[attr-defined]  # TYPE_DEBT: mixin expects GenericViewSet
        tags: list[str] | None = request.data.get("tags")
        if tags:
            for tag in tags:
                tag_obj = create_or_update_tag(tag)
                if tag_obj:
                    m.tags.add(tag_obj)
        serializer = self.get_serializer(m)  # type: ignore[attr-defined]
        return Response(serializer.data)


class TagRemoveMixin:
    """Mixin for removing tags from a model instance.

    Expects the viewset to define queryset, serializer_class, etc.
    The model instance must have a ``.tags`` M2M field.
    """

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        m = self.get_object()  # type: ignore[attr-defined]  # TYPE_DEBT: mixin expects GenericViewSet
        tags: list[int] | None = request.data.get("tags")
        if tags:
            for tag_id in tags:
                t = Tags.objects.get(id=tag_id)
                m.tags.remove(t)
                recalculate_tag_count(t)
        serializer = self.get_serializer(m)  # type: ignore[attr-defined]
        return Response(serializer.data)
