# iam/admin.py
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import Firm, Panel, Membership, FirmPanel, UserPanelPermission
from .permissions import set_current_firm, get_current_firm, is_platform_admin

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)


class FirmPanelInline(admin.TabularInline):
    model = FirmPanel
    extra = 0
    autocomplete_fields = ("panel",)


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "set_current_link")
    search_fields = ("name", "slug")
    inlines = (MembershipInline, FirmPanelInline)

    actions = ["set_as_current_firm"]

    def set_current_link(self, obj):
        return format_html('<a href="{}">Set current</a>', f"../set-current-firm/{obj.pk}/")
    set_current_link.short_description = "Switch"

    def get_urls(self):
        urls = super().get_urls()
        return [
            path("set-current-firm/<int:pk>/", self.admin_site.admin_view(self.set_current_firm_view), name="set_current_firm"),
        ] + urls

    def set_current_firm_view(self, request, pk):
        firm = Firm.objects.get(pk=pk)
        set_current_firm(request, firm)
        messages.success(request, f"Current firm set to: {firm}")
        return redirect("admin:iam_firm_changelist")

    def set_as_current_firm(self, request, queryset):
        firm = queryset.first()
        if not firm:
            self.message_user(request, "Select a firm.", level=messages.WARNING)
            return
        set_current_firm(request, firm)
        self.message_user(request, f"Current firm set to: {firm}", level=messages.SUCCESS)
    set_as_current_firm.short_description = "Set as current firm"


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


class FirmScopedAdminMixin:
    """
    Примесь для моделей, у которых есть FK на firm (например, ваши бизнес-модели).
    Фильтрует queryset по выбранной фирме для не-платформенных пользователей.
    """
    firm_field_name = "firm"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_platform_admin(request.user):
            return qs
        firm = get_current_firm(request)
        if firm is None:
            return qs.none()
        return qs.filter(**{self.firm_field_name: firm})

    # базовые проверки прав (можно ужесточать)
    def has_module_permission(self, request):
        if is_platform_admin(request.user):
            return True
        return get_current_firm(request) is not None

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "firm", "role")
    list_filter = ("role", "firm")
    search_fields = ("user__username", "user__email", "firm__name")


@admin.register(FirmPanel)
class FirmPanelAdmin(admin.ModelAdmin):
    list_display = ("firm", "panel")
    list_filter = ("firm", "panel")


@admin.register(UserPanelPermission)
class UserPanelPermissionAdmin(admin.ModelAdmin):
    list_display = ("membership", "panel", "can_view", "can_edit")
    list_filter = ("panel", "can_view", "can_edit")
    search_fields = ("membership__user__username", "membership__firm__name", "panel__name")
