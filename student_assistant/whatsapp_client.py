"""Send outbound WhatsApp Cloud API messages (synchronous)."""

from __future__ import annotations

import logging
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)


def send_message(to: str, text: str) -> dict[str, Any] | None:
    """Send a text message. `to` is the WhatsApp user id (phone number string)."""
    token = (config.WHATSAPP_TOKEN or "").strip()
    phone_id = (config.PHONE_NUMBER_ID or "").strip()
    if not token or not phone_id:
        logger.warning("WHATSAPP_TOKEN or PHONE_NUMBER_ID not set; skip send.")
        return None

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text[:4096]},
    }
    try:
        # r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.exception("WhatsApp send failed: %s", e)
        return None
