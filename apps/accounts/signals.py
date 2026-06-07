import logging

from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("apps.accounts")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    username = credentials.get("username", "<unknown>")
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = (
        xff.split(",")[-1].strip()
        if xff
        else request.META.get("REMOTE_ADDR", "unknown")
    )
    logger.warning("Failed login attempt for username: %s from IP: %s", username, ip)
