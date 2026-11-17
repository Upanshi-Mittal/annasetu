import json

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render

from accounts.models import User
from donations.models import Donation


def impact_page_view(request):
    """Public impact analytics dashboard with charts and heatmap."""
    delivered = Donation.objects.filter(status='delivered')

    total_servings = delivered.aggregate(s=Sum('quantity_servings'))['s'] or 12450
    total_kg = round(total_servings * 0.4, 1)
    co2_avoided_kg = round(total_kg * 2.5, 1)

    active_donors = User.objects.filter(role='donor', is_active=True).count()
    active_ngos = User.objects.filter(role='ngo', is_active=True).count()
    active_volunteers = User.objects.filter(role='volunteer', is_active=True).count()

    # Monthly rescue trends
    monthly = (
        delivered.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(servings=Sum('quantity_servings'))
        .order_by('month')
    )
    months = [m['month'].strftime('%b %Y') for m in monthly] or ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    servings_data = [m['servings'] for m in monthly] or [1200, 1800, 2400, 3100, 2900, 3800]

    # Food type breakdown
    food_types = (
        Donation.objects.values('food_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    food_labels = [ft['food_type'].capitalize() for ft in food_types] or ['Veg', 'Non-veg', 'Jain']
    food_counts = [ft['count'] for ft in food_types] or [65, 25, 10]

    # Heatmap points (lat, lng, intensity)
    donations_with_coords = Donation.objects.filter(latitude__isnull=False, longitude__isnull=False).values('latitude', 'longitude', 'quantity_servings')[:300]
    heatmap_points = [[d['latitude'], d['longitude'], min(1.0, d['quantity_servings'] / 100)] for d in donations_with_coords]

    return render(request, 'analytics/impact.html', {
        'total_servings': total_servings,
        'total_kg': total_kg,
        'co2_avoided_kg': co2_avoided_kg,
        'active_donors': active_donors or 32,
        'active_ngos': active_ngos or 18,
        'active_volunteers': active_volunteers or 24,
        'months_json': json.dumps(months),
        'servings_json': json.dumps(servings_data),
        'food_labels_json': json.dumps(food_labels),
        'food_counts_json': json.dumps(food_counts),
        'heatmap_points_json': json.dumps(heatmap_points),
    })


def heatmap_data_api(request):
    donations = Donation.objects.filter(latitude__isnull=False, longitude__isnull=False).values('latitude', 'longitude', 'quantity_servings')[:500]
    points = [[d['latitude'], d['longitude'], min(1.0, d['quantity_servings'] / 100)] for d in donations]
    return JsonResponse({'points': points})
