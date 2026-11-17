from django.contrib import admin

from logistics.models import Claim, DeliveryTask, FoodSafetyChecklist, StatusEvent


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'actor', 'timestamp', 'note', 'latitude', 'longitude']
    can_delete = False


@admin.register(DeliveryTask)
class DeliveryTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation', 'volunteer', 'status', 'picked_up_at', 'delivered_at', 'distance_km']
    list_filter = ['status']
    search_fields = ['donation__title', 'volunteer__username']
    inlines = [StatusEventInline]


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation', 'ngo', 'status', 'servings_requested', 'created_at']
    list_filter = ['status']
    search_fields = ['donation__title', 'ngo__username', 'ngo__organization_name']


@admin.register(FoodSafetyChecklist)
class FoodSafetyChecklistAdmin(admin.ModelAdmin):
    list_display = ['task', 'temperature_ok', 'packaging_ok', 'smell_ok', 'within_safe_time', 'completed_by', 'completed_at']


@admin.register(StatusEvent)
class StatusEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation', 'task', 'from_status', 'to_status', 'actor', 'timestamp']
    list_filter = ['from_status', 'to_status']
