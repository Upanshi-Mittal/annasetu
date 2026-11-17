"""
Central notification service — single entry point for all notification channels.
"""
from __future__ import annotations

import logging
from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify(
    user,
    notification_type: str,
    title: str,
    body: str = "",
    url: str = "",
    send_email: bool = True,
    send_ws: bool = True,
    extra_data: Optional[dict] = None,
) -> None:
    """
    Send a notification through all enabled channels:
    1. In-app (database + WebSocket push)
    2. Email (if user has email_notifications enabled)
    3. SMS (if ENABLE_SMS and user has sms_notifications)
    """
    from notifications.models import Notification

    # 1. Create in-app notification
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        body=body,
        url=url,
    )

    # 2. Push via WebSocket
    if send_ws:
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user.id}",
                {
                    "type": "notify",
                    "data": {
                        "id": notification.pk,
                        "type": notification_type,
                        "title": title,
                        "body": body,
                        "url": url,
                        "created_at": notification.created_at.isoformat(),
                        **(extra_data or {}),
                    },
                },
            )
        except Exception:
            logger.exception("Failed to send WebSocket notification to user %s", user.pk)

    # 3. Email
    if send_email and user.email_notifications and user.email:
        try:
            send_mail(
                subject=f"[AnnaSetu] {title}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send email to user %s", user.pk)

    # 4. SMS (behind feature flag)
    if settings.ENABLE_SMS and user.sms_notifications and user.phone:
        _send_sms(user.phone, f"{title}: {body}")


def _send_sms(phone: str, message: str) -> None:
    """Send SMS via Twilio or console fallback."""
    try:
        from twilio.rest import Client

        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
    except ImportError:
        logger.info("Twilio not installed — SMS to %s: %s", phone, message)
    except Exception:
        logger.exception("SMS send failed to %s", phone)


def broadcast_donation_feed(donation_data: dict) -> None:
    """Broadcast a new donation to the live feed WebSocket channel."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "donation_feed",
            {
                "type": "new_donation",
                "data": donation_data,
            },
        )
    except Exception:
        logger.exception("Failed to broadcast donation feed")


def broadcast_task_update(task_id: int, data: dict) -> None:
    """Push a task status update to the tracking WebSocket channel."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task_update",
                "data": data,
            },
        )
    except Exception:
        logger.exception("Failed to broadcast task update %s", task_id)
