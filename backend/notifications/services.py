from django.utils import timezone

from notifications.models import Notification


def create_notification(
    *,
    recipient,
    notification_type,
    title,
    message,
    complaint=None,
    metadata=None,
):
    """
    Create one in-app notification for a user.

    Notification creation is intentionally simple and
    non-AI dependent so it remains reliable even when
    external AI services are unavailable.
    """

    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        complaint=complaint,
        metadata=metadata or {},
    )


def mark_notification_read(
    *,
    notification,
):
    """
    Mark one notification as read.
    """

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(
            update_fields=[
                "is_read",
                "read_at",
            ]
        )

    return notification


def mark_all_notifications_read(
    *,
    recipient,
):
    """
    Mark all unread notifications belonging to
    a recipient as read.
    """

    return Notification.objects.filter(
        recipient=recipient,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )


def notify_complaint_user(
    *,
    complaint,
    notification_type,
    title,
    message,
    metadata=None,
):
    """
    Send a notification to the citizen who created
    the complaint.
    """

    if complaint.user_id is None:
        return None

    return create_notification(
        recipient=complaint.user,
        notification_type=notification_type,
        title=title,
        message=message,
        complaint=complaint,
        metadata=metadata,
    )


def notify_assigned_officer(
    *,
    complaint,
    notification_type,
    title,
    message,
    metadata=None,
):
    """
    Send a notification to the currently assigned
    officer, if one exists.
    """

    assignment = (
        complaint.assignments
        .filter(
            unassigned_at__isnull=True,
        )
        .select_related("officer")
        .first()
    )

    if assignment is None or assignment.officer_id is None:
        return None

    return create_notification(
        recipient=assignment.officer,
        notification_type=notification_type,
        title=title,
        message=message,
        complaint=complaint,
        metadata=metadata,
    )


def notify_active_admins(
    *,
    notification_type,
    title,
    message,
    complaint=None,
    metadata=None,
):
    """
    Send a system notification to all active
    administrators.
    """

    from accounts.models import User

    admins = User.objects.filter(
        role=User.Role.ADMIN,
        is_active=True,
    )

    notifications = []

    for admin in admins:
        notifications.append(
            create_notification(
                recipient=admin,
                notification_type=notification_type,
                title=title,
                message=message,
                complaint=complaint,
                metadata=metadata,
            )
        )

    return notifications