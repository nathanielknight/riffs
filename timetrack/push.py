"""Web Push (VAPID) helpers for timetrack reminders."""

import base64
import json
import logging

from constance import config
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from .models import PushSubscription

logger = logging.getLogger(__name__)


def _get_vapid():
    """Load the VAPID key pair, generating and storing one on first use."""
    pem = config.TIMETRACK_VAPID_PRIVATE_KEY
    if not pem:
        vapid = Vapid()
        vapid.generate_keys()
        pem = vapid.private_pem().decode()
        # Assigning to a constance setting persists it to the database.
        config.TIMETRACK_VAPID_PRIVATE_KEY = pem
    return Vapid.from_pem(pem.encode())


def public_key():
    """The application server key browsers need to subscribe (base64url)."""
    raw = _get_vapid().public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def send_to_all(title, body, url="/timetrack/"):
    """Send a notification to every subscription; prune dead ones.

    Returns the number of devices the notification was delivered to.
    """
    vapid = _get_vapid()
    payload = json.dumps({"title": title, "body": body, "url": url})
    sent = 0
    for sub in PushSubscription.objects.all():
        try:
            webpush(
                sub.as_subscription_info(),
                payload,
                vapid_private_key=vapid,
                vapid_claims={"sub": config.TIMETRACK_PUSH_CONTACT},
            )
            sent += 1
        except WebPushException as e:
            status = e.response.status_code if e.response is not None else None
            if status in (404, 410):
                sub.delete()
            else:
                logger.warning("Push to %s failed: %s", sub, e)
    return sent
