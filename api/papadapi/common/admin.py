from django.contrib import admin

from papadapi.common.models import Group, Tags


class BaseAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        # Disable delete
        return False

    def has_change_permission(self, request, obj=None):
        # Disable delete
        return False

    @admin.display(
        description="UUID",
        ordering="uuid",
    )
    def get_uuid_formatted(self, obj):
        if obj:
            return str(obj.uuid)



@admin.register(Group)
class GroupAdmin(BaseAdmin):
    list_display = ("name", "is_active", "is_public", "created_at", "updated_at")
    list_filter = ("is_active", "is_public")


@admin.register(Tags)
class TagAdmin(BaseAdmin):
    list_display = ("name", "count", "created_at", "updated_at")


