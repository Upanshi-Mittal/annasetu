from django.contrib import admin

from moderation.models import Report


@admin.action(description="Mark selected reports as Resolved")
def resolve_reports(modeladmin, request, queryset):
    queryset.update(status='resolved', resolved_by=request.user)


@admin.action(description="Dismiss selected reports")
def dismiss_reports(modeladmin, request, queryset):
    queryset.update(status='dismissed', resolved_by=request.user)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reporter', 'target_user', 'target_donation', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason']
    search_fields = ['description', 'reporter__username']
    actions = [resolve_reports, dismiss_reports]
