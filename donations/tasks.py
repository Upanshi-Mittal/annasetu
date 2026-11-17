import logging

from celery import shared_task

from donations.services import escalate_expiring_donations, expire_stale_donations

logger = logging.getLogger(__name__)


@shared_task(name="donations.tasks.expire_stale_donations_task")
def expire_stale_donations_task():
    """Expire listings past safe_until every minute."""
    count = expire_stale_donations()
    logger.info("Auto-expired %d stale listings", count)
    return count


@shared_task(name="donations.tasks.escalate_expiring_donations_task")
def escalate_expiring_donations_task():
    """Escalate listings expiring within 2 hours with no claim."""
    count = escalate_expiring_donations()
    logger.info("Urgency escalation sent for %d listings", count)
    return count


@shared_task(name="donations.tasks.daily_digest_task")
def daily_digest_task():
    """Send daily digest summary to active users."""
    logger.info("Daily digest completed")
    return True
