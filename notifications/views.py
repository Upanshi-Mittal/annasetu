from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })


@login_required
def notification_mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if request.headers.get('HX-Request'):
        return render(request, 'notifications/partials/notification_item.html', {'notification': notification})
    if notification.url:
        return redirect(notification.url)
    return redirect('notification_list')


@login_required
def notification_mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('HX-Request'):
        return JsonResponse({'status': 'ok'})
    return redirect('notification_list')
