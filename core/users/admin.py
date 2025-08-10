from django.contrib import admin
from django.db.models import F
from .models import (
    Plan, Subscription, Scanner, PlanScannerAccess, PlanToolAccess,
    Coupon, CouponRedemption, IntegrationPartner, PlanIntegration,
    ToolUsageLimit, ToolUsageCounter
)
from main.models import ToolPage  # если ToolPage в другом app


class PlanScannerAccessInline(admin.TabularInline):
    model = PlanScannerAccess
    extra = 1
    autocomplete_fields = ['scanner']
    fields = ['scanner', 'included', 'extra_price']
    verbose_name = "Scanner Access"
    verbose_name_plural = "Scanner Accesses"


class PlanToolAccessInline(admin.TabularInline):
    model = PlanToolAccess
    extra = 1
    autocomplete_fields = ['tool']
    fields = ['tool', 'included', 'extra_price']
    verbose_name = "Tool Access"
    verbose_name_plural = "Tool Accesses"


class PlanIntegrationInline(admin.TabularInline):
    model = PlanIntegration
    extra = 0
    autocomplete_fields = ['partner']
    fields = ['partner', 'included', 'monthly_limit', 'overage_price']
    verbose_name = "Integration"
    verbose_name_plural = "Integrations"


class ToolUsageLimitInline(admin.TabularInline):
    model = ToolUsageLimit
    extra = 0
    autocomplete_fields = ['tool']
    fields = ['tool', 'period', 'limit', 'overage_price']
    verbose_name = "Tool Usage Limit"
    verbose_name_plural = "Tool Usage Limits"


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'monthly_price',
        'yearly_price',
        'monthly_attempts_limit',
        'yearly_attempts_limit',
    )
    search_fields = ('name', 'slug')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Prices', {
            'fields': ('monthly_price', 'yearly_price')
        }),
        ('Limits', {
            'fields': ('monthly_attempts_limit', 'yearly_attempts_limit')
        }),
        ('Features', {
            'fields': ('monthly_features', 'yearly_features')
        }),
    )


    inlines = [
        PlanScannerAccessInline,
        PlanToolAccessInline,
        PlanIntegrationInline,
        ToolUsageLimitInline,
    ]


@admin.action(description="Reset attempts for selected subscriptions (monthly/yearly by period)")
def reset_attempts(modeladmin, request, queryset):
    for sub in queryset:
        sub.reset_attempts()


@admin.action(description="Expire selected subscriptions now")
def force_expire(modeladmin, request, queryset):
    updated = queryset.update(status='expired')
    modeladmin.message_user(request, f"Expired: {updated}")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'plan', 'status', 'is_trial', 'auto_renew', 'attempts_left',
        'start_date', 'end_date', 'remaining_days', 'times_renewed',
        'payment_method', 'transaction_id', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'is_trial', 'auto_renew', 'payment_method', 'plan')
    search_fields = ('user__username', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'remaining_days')
    ordering = ('-created_at',)
    actions = [reset_attempts, force_expire]


@admin.register(Scanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'command')
    search_fields = ('name', 'command')
    ordering = ('name',)


@admin.register(PlanScannerAccess)
class PlanScannerAccessAdmin(admin.ModelAdmin):
    list_display = ('plan', 'scanner', 'included', 'extra_price')
    list_filter = ('included', 'plan')
    search_fields = ('plan__name', 'scanner__name')
    autocomplete_fields = ['plan', 'scanner']


# ===== Coupons / Discounts =====

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'value', 'is_active',
        'valid_from', 'valid_to', 'usage_count', 'max_uses', 'per_user_limit', 'stackable'
    )
    list_filter = ('is_active', 'discount_type', 'stackable')
    search_fields = ('code', 'description')
    filter_horizontal = ('plans', 'tools')
    readonly_fields = ('usage_count', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'discount_type', 'value', 'is_active', 'stackable')
        }),
        ('Applicability', {
            'fields': ('plans', 'tools')
        }),
        ('Limits & Window', {
            'fields': ('valid_from', 'valid_to', 'max_uses', 'per_user_limit', 'usage_count')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'plan', 'subscription', 'amount_discounted', 'created_at')
    list_filter = ('coupon', 'plan')
    search_fields = ('coupon__code', 'user__username')
    autocomplete_fields = ['coupon', 'user', 'plan', 'subscription']
    readonly_fields = ('created_at',)


# ===== Integrations =====

@admin.register(IntegrationPartner)
class IntegrationPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(PlanIntegration)
class PlanIntegrationAdmin(admin.ModelAdmin):
    list_display = ('plan', 'partner', 'included', 'monthly_limit', 'overage_price')
    list_filter = ('plan', 'partner', 'included')
    search_fields = ('plan__name', 'partner__name')
    autocomplete_fields = ['plan', 'partner']


# ===== Tool usage limits & counters =====

@admin.register(ToolUsageLimit)
class ToolUsageLimitAdmin(admin.ModelAdmin):
    list_display = ('plan', 'tool', 'period', 'limit', 'overage_price')
    list_filter = ('plan', 'period')
    search_fields = ('plan__name', 'tool__title')
    autocomplete_fields = ['plan', 'tool']


@admin.register(ToolUsageCounter)
class ToolUsageCounterAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'tool', 'period', 'used', 'window_started_at')
    list_filter = ('period', 'tool')
    search_fields = ('subscription__user__username', 'tool__title')
    autocomplete_fields = ['subscription', 'tool']
    readonly_fields = ('window_started_at',)
