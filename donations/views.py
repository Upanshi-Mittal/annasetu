from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from donations.forms import ClaimForm, DonationForm
from donations.models import Donation
from donations.services import transition_donation
from matching.geo import filter_by_distance
from matching.services import compute_match_scores
from notifications.services import broadcast_donation_feed


def donation_list_view(request):
    """Discovery feed with HTMX search, filtering, sorting, distance slider, and map toggle."""
    qs = Donation.objects.filter(status='posted').select_related('donor')

    # Filters
    food_type = request.GET.get('food_type')
    if food_type:
        qs = qs.filter(food_type=food_type)

    is_cooked = request.GET.get('is_cooked')
    if is_cooked in ['true', 'false']:
        qs = qs.filter(is_cooked=(is_cooked == 'true'))

    urgency = request.GET.get('urgency')
    if urgency == 'urgent':
        # items expiring in < 2h
        from django.utils import timezone
        qs = qs.filter(safe_until__lte=timezone.now() + timezone.timedelta(hours=2))

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'expiring':
        qs = qs.order_by('safe_until')
    elif sort == 'quantity':
        qs = qs.order_by('-quantity_servings')
    else:
        qs = qs.order_by('-created_at')

    # Distance filtering if user has location
    user = request.user
    distance_km = request.GET.get('distance')
    if distance_km and user.is_authenticated and user.latitude and user.longitude:
        try:
            dist_val = float(distance_km)
            nearby_items = filter_by_distance(qs, user.latitude, user.longitude, dist_val)
            qs = [item[0] for item in nearby_items]
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    template = 'donations/partials/donation_cards.html' if request.headers.get('HX-Request') else 'donations/donation_list.html'
    return render(request, template, {
        'page_obj': page_obj,
        'view_mode': request.GET.get('view', 'list'),
    })


def donation_detail_view(request, pk):
    donation = get_object_or_404(Donation.objects.select_related('donor'), pk=pk)
    claim_form = ClaimForm(initial={'servings_requested': donation.quantity_servings})

    # Check if user is verified NGO or admin
    can_claim = False
    if request.user.is_authenticated and request.user.is_ngo and request.user.is_verified and donation.status == 'posted':
        can_claim = True

    # Smart matching breakdown for admins / donor
    match_breakdown = None
    if request.user.is_staff or request.user == donation.donor:
        match_breakdown = compute_match_scores(donation)

    return render(request, 'donations/donation_detail.html', {
        'donation': donation,
        'claim_form': claim_form,
        'can_claim': can_claim,
        'match_breakdown': match_breakdown,
    })


@login_required
def donation_create_view(request):
    if not (request.user.is_donor or request.user.is_staff):
        messages.error(request, _('Only donors can post food donations.'))
        return redirect('donation_list')

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            if not donation.latitude and request.user.latitude:
                donation.latitude = request.user.latitude
                donation.longitude = request.user.longitude
            donation.save()

            # Broadcast over WebSocket
            broadcast_donation_feed({
                'id': donation.id,
                'title': donation.title,
                'servings': donation.quantity_servings,
                'food_type': donation.food_type,
                'pickup_address': donation.pickup_address,
                'time_left_seconds': donation.time_left_seconds,
            })

            messages.success(request, _('Your food donation has been posted successfully!'))
            return redirect('donation_detail', pk=donation.pk)
    else:
        initial = {}
        if request.user.address:
            initial['pickup_address'] = request.user.address
        if request.user.latitude:
            initial['latitude'] = request.user.latitude
            initial['longitude'] = request.user.longitude
        form = DonationForm(initial=initial)

    return render(request, 'donations/donation_form.html', {'form': form})


@login_required
def donation_edit_view(request, pk):
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    if donation.status != 'posted':
        messages.error(request, _('Cannot edit a donation that has already been claimed or processed.'))
        return redirect('donation_detail', pk=pk)

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, _('Donation updated successfully.'))
            return redirect('donation_detail', pk=pk)
    else:
        form = DonationForm(instance=donation)

    return render(request, 'donations/donation_form.html', {'form': form, 'donation': donation})


@login_required
def donation_cancel_view(request, pk):
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    if request.method == 'POST':
        try:
            transition_donation(donation, 'cancelled', actor=request.user, note="Cancelled by donor")
            messages.info(request, _('Donation cancelled.'))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('donation_detail', pk=pk)
