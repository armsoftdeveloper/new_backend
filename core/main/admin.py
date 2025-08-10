from django.contrib import admin
from .models import *

class ToolBlockInline(admin.TabularInline):
    model = ToolBlock
    extra = 1

@admin.register(ToolPage)
class ToolPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'subcategory', 'created_at')
    search_fields = ('title',)

@admin.register(LandingContent)
class LandingContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_published', 'created_by', 'updated_by', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Banner)

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_by', 'updated_by', 'created_at', 'updated_at')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'is_published')}),
        ('Metadata', {'classes': ('collapse',), 'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    search_fields = ('title', 'description',)
    list_filter = ('is_published', 'created_by', 'updated_by', 'created_at', 'updated_at',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TeamService)
class TeamServiceAdmin(admin.ModelAdmin):
    list_display = ['team', 'description', 'updated_at']
    list_filter = ['team']
    search_fields = ['team', 'description']
    readonly_fields = ['updated_at']

@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_by', 'updated_by', 'created_at', 'updated_at')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'icon_key', 'image', 'is_published')}),
        ('Metadata', {'classes': ('collapse',), 'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    search_fields = ('title', 'description',)
    list_filter = ('is_published', 'created_by', 'updated_by', 'created_at', 'updated_at',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'suffix' , 'is_published', 'created_by', 'updated_by', 'created_at', 'updated_at')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'value', 'suffix' , 'is_published')}),
        ('Metadata', {'classes': ('collapse',), 'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    search_fields = ('title',)
    list_filter = ('is_published', 'created_by', 'updated_by', 'created_at', 'updated_at',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('email', 'twitter_url', 'github_url', 'linkedin_url', 'updated_at')
    readonly_fields = ('updated_at',)

@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')

@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')

@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    readonly_fields = ("name", "email", "message", "created_at")
    search_fields = ("name", "email")
    ordering = ("-created_at",)

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    ordering = ('-subscribed_at',)

@admin.register(LandingSlider)
class LandingSliderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_published', 'time_create', 'time_update']
    readonly_fields = ['time_create', 'time_update']
    list_filter = ['is_published', 'time_create']
