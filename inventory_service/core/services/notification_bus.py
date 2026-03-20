"""Single entry point for email and in-app notifications. Persists Notification and enqueues delivery."""

import logging

from inventory_service.audit.models import Notification
from inventory_service.audit.tasks import send_notification_email

logger = logging.getLogger(__name__)


class NotificationBus:
    def send(
        self,
        recipient_id,
        notification_type="email",
        title="",
        message="",
        data=None,
        corporate_id=None,
    ):
        """Persist a Notification and enqueue async email if type is email. data can include 'email' for destination."""
        data = data or {}
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            corporate_id=corporate_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data,
        )
        if notification_type == "email":
            send_notification_email.delay(str(notification.id))
        return notification

    def send_email(self, recipient_id, subject, body, destination_email=None, corporate_id=None):
        """Convenience: send an email notification. Pass destination_email in data for delivery."""
        data = {}
        if destination_email:
            data["email"] = destination_email
        return self.send(
            recipient_id=recipient_id,
            notification_type="email",
            title=subject,
            message=body,
            data=data,
            corporate_id=corporate_id,
        )
