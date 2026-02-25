from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin, messages

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

from papadapi.annotate.models import Annotation
from papadapi.common.admin import BaseAdmin


@admin.register(Annotation)
class AnnotationAdmin(BaseAdmin):
    list_display = (
        "get_uuid_formatted",
        "media_reference_id",
        "annotation_text",
        "is_delete",
        "created_at",
        "updated_at",
        "is_instance_admin_withheld",
    )
    list_filter = ("media_reference_id", "is_delete", "is_instance_admin_withheld")
    actions = ["admin_withhold_annotation", "admin_unblock_annotation"]

    @admin.action(description="Withhold selected annotation")
    def admin_withhold_annotation(
        self, request: HttpRequest, queryset: QuerySet[Annotation],
    ) -> None:

        queryset.update(is_instance_admin_withheld=True)
        queryset.update(is_delete=True)
        self.message_user(
            request, "selected annotation successfully withheld", messages.SUCCESS
        )

    @admin.action(description="Unblock selected annotation")
    def admin_unblock_annotation(
        self, request: HttpRequest, queryset: QuerySet[Annotation],
    ) -> None:

        queryset.update(is_instance_admin_withheld=False)
        queryset.update(is_delete=False)
        self.message_user(
            request, "selected meida successfully unblocked", messages.SUCCESS
        )
