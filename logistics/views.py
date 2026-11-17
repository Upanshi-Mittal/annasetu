import base64
import io

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from donations.forms import ClaimForm, FoodSafetyChecklistForm
from donations.models import Donation
from logistics.models import Claim, DeliveryTask, FoodSafetyChecklist, StatusEvent
from logistics.services import accept_claim, accept_task, confirm_delivery, confirm_pickup, create_claim, verify_qr_scan


def _generate_qr_svg_or_base64(token_str):
    """Generate QR code image as base64 data URI."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(token_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"


@login_required
def claim_create_view(request, donation_id):
    donation = get_object_or_404(Donation, pk=donation_id)
    if not (request.user.is_ngo and request.user.is_verified):
        messages.error(request, _('Only verified NGOs can claim donations.'))
        return redirect('donation_detail', pk=donation_id)

    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            try:
                claim, task = create_claim(
                    donation=donation,
                    ngo=request.user,
                    servings_requested=form.cleaned_data['servings_requested'],
                    note=form.cleaned_data.get('note', '')
                )
                if task:
                    messages.success(request, _('Claim auto-accepted! Delivery task created.'))
                    return redirect('task_detail', pk=task.pk)
                else:
                    messages.success(request, _('Claim submitted! Awaiting donor confirmation.'))
                    return redirect('donation_detail', pk=donation.pk)
            except ValueError as e:
                messages.error(request, str(e))
    return redirect('donation_detail', pk=donation_id)


@login_required
def claim_accept_view(request, claim_id):
    claim = get_object_or_404(Claim, pk=claim_id)
    if request.user != claim.donation.donor and not request.user.is_staff:
        messages.error(request, _('You are not authorized to accept this claim.'))
        return redirect('donation_detail', pk=claim.donation.pk)

    if request.method == 'POST':
        try:
            task = accept_claim(claim, request.user)
            messages.success(request, _('Claim accepted! Delivery task created.'))
            return redirect('task_detail', pk=task.pk)
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('donation_detail', pk=claim.donation.pk)


@login_required
def task_list_view(request):
    user = request.user
    if user.is_volunteer:
        my_tasks = DeliveryTask.objects.filter(volunteer=user).select_related('donation', 'claim')
        open_tasks = DeliveryTask.objects.filter(status='pending').select_related('donation', 'claim')
    elif user.is_ngo:
        my_tasks = DeliveryTask.objects.filter(claim__ngo=user).select_related('donation', 'claim')
        open_tasks = DeliveryTask.objects.none()
    elif user.is_donor:
        my_tasks = DeliveryTask.objects.filter(donation__donor=user).select_related('donation', 'claim')
        open_tasks = DeliveryTask.objects.none()
    else:
        my_tasks = DeliveryTask.objects.all().select_related('donation', 'claim')[:50]
        open_tasks = DeliveryTask.objects.filter(status='pending')[:20]

    return render(request, 'logistics/task_list.html', {
        'my_tasks': my_tasks,
        'open_tasks': open_tasks,
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(
        DeliveryTask.objects.select_related('donation', 'claim', 'volunteer', 'donation__donor', 'claim__ngo'),
        pk=pk
    )
    checklist_form = FoodSafetyChecklistForm()
    checklist = getattr(task, 'safety_checklist', None)

    # Generate QR codes for pickup and delivery
    pickup_qr_image = _generate_qr_svg_or_base64(task.pickup_qr_token)
    delivery_qr_image = _generate_qr_svg_or_base64(task.delivery_qr_token)

    timeline_events = StatusEvent.objects.filter(
        donation=task.donation
    ).select_related('actor').order_by('timestamp')

    return render(request, 'logistics/task_detail.html', {
        'task': task,
        'checklist': checklist,
        'checklist_form': checklist_form,
        'pickup_qr_image': pickup_qr_image,
        'delivery_qr_image': delivery_qr_image,
        'timeline_events': timeline_events,
    })


@login_required
def task_accept_view(request, pk):
    task = get_object_or_404(DeliveryTask, pk=pk)
    if not (request.user.is_volunteer or request.user.is_ngo or request.user.is_staff):
        messages.error(request, _('Only volunteers or NGOs can accept delivery tasks.'))
        return redirect('task_detail', pk=pk)

    if request.method == 'POST':
        try:
            accept_task(task, request.user)
            messages.success(request, _('Task assigned to you! Please review pickup details.'))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('task_detail', pk=pk)


@login_required
def task_safety_checklist_view(request, pk):
    task = get_object_or_404(DeliveryTask, pk=pk)
    if request.method == 'POST':
        form = FoodSafetyChecklistForm(request.POST)
        if form.is_valid():
            FoodSafetyChecklist.objects.update_or_create(
                task=task,
                defaults={
                    'temperature_ok': form.cleaned_data['temperature_ok'],
                    'packaging_ok': form.cleaned_data['packaging_ok'],
                    'smell_ok': form.cleaned_data['smell_ok'],
                    'within_safe_time': form.cleaned_data['within_safe_time'],
                    'notes': form.cleaned_data.get('notes', ''),
                    'completed_by': request.user,
                }
            )
            messages.success(request, _('Food safety checklist verified!'))
        else:
            messages.error(request, _('Please check and confirm all safety criteria.'))
    return redirect('task_detail', pk=pk)


@login_required
def task_scan_qr_view(request, pk):
    """Scan and verify pickup or delivery QR code."""
    task = get_object_or_404(DeliveryTask, pk=pk)

    if request.method == 'POST':
        token = request.POST.get('qr_token')
        scan_type = request.POST.get('scan_type')  # 'pickup' or 'delivery'

        token_data = verify_qr_scan(token)
        if not token_data:
            messages.error(request, _('Invalid or expired QR code token.'))
            return redirect('task_detail', pk=pk)

        try:
            if scan_type == 'pickup':
                confirm_pickup(task, request.user)
                messages.success(request, _('Pickup confirmed! You may now proceed to delivery.'))
            elif scan_type == 'delivery':
                confirm_delivery(task, request.user)
                messages.success(request, _('Delivery confirmed! Thank you for rescuing food!'))
        except ValueError as e:
            messages.error(request, str(e))

    return redirect('task_detail', pk=pk)
