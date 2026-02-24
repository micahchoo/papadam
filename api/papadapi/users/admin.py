from django.contrib import admin, messages
from django.contrib.auth.models import Group

from papadapi.common.admin import BaseAdmin
from papadapi.users.models import User

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ("name", "username", "is_active", "last_login", "date_joined")
    list_filter = ("is_superuser",)
    actions = ["admin_withhold_user", "admin_unblock_user"]

    @admin.action(description="Withhold selected user")
    def admin_withhold_user(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(
            request, "selected User successfully withheld", messages.SUCCESS
        )

    @admin.action(description="Unblock selected user")
    def admin_unblock_user(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(
            request, "selected User successfully unblocked", messages.SUCCESS
        )

    @admin.display(
        description="Full Name"
    )
    def name(self, obj):
        if obj:
            return str(obj.first_name + obj.last_name)



