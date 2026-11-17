from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from donations.forms import RatingForm
from gamification.models import Badge, Rating
from logistics.models import DeliveryTask


def leaderboard_view(request):
    """City & all-time volunteer and donor leaderboards."""
    top_volunteers = (
        User.objects.filter(role='volunteer')
        .annotate(points=Sum('points_ledger__points'))
        .order_by('-points')[:20]
    )
    top_donors = (
        User.objects.filter(role='donor')
        .annotate(donations_count=Count('donations'))
        .order_by('-donations_count')[:20]
    )
    all_badges = Badge.objects.all()

    return render(request, 'gamification/leaderboard.html', {
        'top_volunteers': top_volunteers,
        'top_donors': top_donors,
        'all_badges': all_badges,
    })


@login_required
def rate_task_view(request, task_id):
    task = get_object_or_404(DeliveryTask, pk=task_id)
    if task.status != 'delivered':
        messages.error(request, _('You can only rate completed deliveries.'))
        return redirect('task_detail', pk=task_id)

    # Determine recipient
    if request.user == task.donation.donor:
        to_user = task.volunteer or task.claim.ngo
    elif request.user == task.claim.ngo:
        to_user = task.donation.donor
    elif request.user == task.volunteer:
        to_user = task.donation.donor
    else:
        messages.error(request, _('You are not a participant in this delivery.'))
        return redirect('task_detail', pk=task_id)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            score = form.cleaned_data['score']
            comment = form.cleaned_data.get('comment', '')
            Rating.objects.update_or_create(
                from_user=request.user,
                task=task,
                defaults={
                    'to_user': to_user,
                    'score': score,
                    'comment': comment,
                }
            )

            # Update recipient's reliability score (weighted moving average)
            avg = Rating.objects.filter(to_user=to_user).aggregate(Sum('score'))['score__sum']
            cnt = Rating.objects.filter(to_user=to_user).count()
            if cnt > 0:
                to_user.reliability_score = round(avg / cnt, 2)
                to_user.save(update_fields=['reliability_score'])

            messages.success(request, _('Thank you for rating!'))
            return redirect('task_detail', pk=task_id)
    else:
        form = RatingForm()

    return render(request, 'gamification/rate_task.html', {
        'task': task,
        'to_user': to_user,
        'form': form,
    })
