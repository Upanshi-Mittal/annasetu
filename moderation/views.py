from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from donations.forms import ReportForm
from donations.models import Donation
from moderation.models import Report


@login_required
def report_create_view(request):
    """File a report against a user or donation."""
    target_user_id = request.GET.get('user_id')
    donation_id = request.GET.get('donation_id')

    target_user = get_object_or_404(User, pk=target_user_id) if target_user_id else None
    target_donation = get_object_or_404(Donation, pk=donation_id) if donation_id else None

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            Report.objects.create(
                reporter=request.user,
                target_user=target_user,
                target_donation=target_donation,
                reason=form.cleaned_data['reason'],
                description=form.cleaned_data['description'],
            )
            messages.success(request, _('Your report has been submitted. Our moderation team will investigate.'))
            return redirect('dashboard')
    else:
        form = ReportForm()

    return render(request, 'moderation/report_form.html', {
        'form': form,
        'target_user': target_user,
        'target_donation': target_donation,
    })
