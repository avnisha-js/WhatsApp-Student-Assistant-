"""Environment-driven settings for WhatsApp webhook."""

import os

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "change-me")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
