from django.contrib import admin

from donations.models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['title', 'donor', 'food_type', 'is_cooked', 'quantity_servings', 'status', 'safe_until', 'created_at']
    list_filter = ['status', 'food_type', 'is_cooked']
    search_fields = ['title', 'pickup_address', 'donor__username', 'donor__organization_name']
    date_hierarchy = 'created_at'
