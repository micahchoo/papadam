from django.contrib import admin, messages

from papadapi.archive.models import MediaStore
from papadapi.common.admin import BaseAdmin


@admin.register(MediaStore)
class MediaStoreAdmin(BaseAdmin):
    list_display = (
        "get_uuid_formatted",
        "name",
        "group",
        "is_delete",
        "created_at",
        "updated_at",
        "is_instance_admin_withheld",
    )
    list_filter = ("group", "is_delete", "is_instance_admin_withheld")
    actions = ["admin_withhold_media", "admin_unblock_media"]

    @admin.action(description="Withhold selected media")
    def admin_withhold_media(self, request, queryset):

        queryset.update(is_instance_admin_withheld=True)
        queryset.update(is_delete=True)
        self.message_user(
            request, "selected media successfully withheld", messages.SUCCESS
        )

    @admin.action(description="Unblock selected media")
    def admin_unblock_media(self, request, queryset):

        queryset.update(is_instance_admin_withheld=False)
        queryset.update(is_delete=False)
        self.message_user(
            request, "selected meida successfully unblocked", messages.SUCCESS
        )


admin.site.disable_action("delete_selected")
