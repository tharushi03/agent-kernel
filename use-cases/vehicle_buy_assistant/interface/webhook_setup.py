# interface/webhook_setup.py
"""
Meta WhatsApp Webhook Setup — Reference Implementation
=======================================================
This file demonstrates a complete understanding of the Meta (Facebook)
WhatsApp Cloud API webhook protocol.

Even without a live Meta Business account, this code shows:
  1. Webhook verification (GET hub.challenge handshake)
  2. Signature validation (X-Hub-Signature-256 HMAC check)
  3. Incoming message parsing (text, interactive, media)
  4. Outgoing message sending via Meta Graph API
  5. How Agent Kernel's AgentWhatsAppRequestHandler replaces all of this

In production, Agent Kernel handles steps 1–5 automatically.
This file exists to demonstrate knowledge of the underlying protocol.

References:
  https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks
  https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
"""

import os
import hmac
import hashlib
import json
import requests


# ── Configuration (loaded from environment variables) ─────────────────────────

VERIFY_TOKEN = os.environ.get("AK_WHATSAPP__VERIFY_TOKEN", "your_verify_token")
ACCESS_TOKEN = os.environ.get("AK_WHATSAPP__ACCESS_TOKEN", "your_access_token")
PHONE_NUMBER_ID = os.environ.get("AK_WHATSAPP__PHONE_NUMBER_ID", "your_phone_id")
APP_SECRET = os.environ.get("META_APP_SECRET", "your_app_secret")
API_VERSION = os.environ.get("AK_WHATSAPP__API_VERSION", "v21.0")

GRAPH_API_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Webhook Verification (GET request from Meta)
# ─────────────────────────────────────────────────────────────────────────────

def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> tuple:
    """
    Handle the GET request Meta sends when you configure a webhook in the
    Meta Developer Portal.

    Meta sends:
      GET /webhook?hub.mode=subscribe
                  &hub.verify_token=<YOUR_VERIFY_TOKEN>
                  &hub.challenge=<RANDOM_STRING>

    Your server must respond with the hub.challenge value to confirm ownership.

    Args:
        hub_mode:         Should be "subscribe"
        hub_verify_token: Must match your VERIFY_TOKEN env variable
        hub_challenge:    Echo this value back with HTTP 200

    Returns:
        (response_body, http_status_code)
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print(f"[Webhook] Verification successful. Echoing challenge.")
        return hub_challenge, 200

    print(f"[Webhook] Verification FAILED. Token mismatch.")
    return "Forbidden", 403


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Signature Validation (POST request security)
# ─────────────────────────────────────────────────────────────────────────────

def validate_signature(raw_body: bytes, x_hub_signature_256: str) -> bool:
    """
    Validate the X-Hub-Signature-256 header on every incoming POST request.

    Meta signs every webhook POST with HMAC-SHA256 using your App Secret.
    Always validate this to reject forged requests.

    Header format: "sha256=<hex_digest>"

    Args:
        raw_body:              The raw bytes of the HTTP request body
        x_hub_signature_256:   The X-Hub-Signature-256 header value from Meta

    Returns:
        True if signature is valid, False otherwise
    """
    if not x_hub_signature_256 or not x_hub_signature_256.startswith("sha256="):
        return False

    expected = hmac.new(
        APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    received = x_hub_signature_256[len("sha256="):]

    # Use hmac.compare_digest to prevent timing attacks
    return hmac.compare_digest(expected, received)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Parse Incoming Webhook Payload (POST from Meta)
# ─────────────────────────────────────────────────────────────────────────────

def parse_incoming_message(payload: dict) -> dict | None:
    """
    Extract sender phone number and message text from the Meta webhook payload.

    Meta webhook payload structure:
    {
      "object": "whatsapp_business_account",
      "entry": [{
        "changes": [{
          "value": {
            "contacts": [{"wa_id": "94771234567", ...}],
            "messages": [{
              "from": "94771234567",
              "id": "wamid.xxx",
              "type": "text",
              "text": {"body": "Hello!"}
            }]
          }
        }]
      }]
    }

    Args:
        payload: Parsed JSON dict from the incoming POST body

    Returns:
        {"phone": "94771234567", "text": "Hello!", "message_id": "wamid.xxx"}
        or None if no valid message found
    """
    try:
        entry = payload.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None  # Could be a status update, not a user message

        msg = messages[0]
        phone = msg.get("from", "")
        message_id = msg.get("id", "")
        msg_type = msg.get("type", "")

        # Handle text messages
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "").strip()
            return {"phone": phone, "text": text, "message_id": message_id}

        # Handle interactive replies (button clicks)
        if msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive["button_reply"].get("title", "")
                return {"phone": phone, "text": text, "message_id": message_id}
            if interactive.get("type") == "list_reply":
                text = interactive["list_reply"].get("title", "")
                return {"phone": phone, "text": text, "message_id": message_id}

        print(f"[Webhook] Unhandled message type: {msg_type}")
        return None

    except (IndexError, KeyError, TypeError) as e:
        print(f"[Webhook] Error parsing payload: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Send Reply via Meta Graph API
# ─────────────────────────────────────────────────────────────────────────────

def send_text_message(to_phone: str, message: str) -> bool:
    """
    Send a plain text reply back to the user via the Meta Graph API.

    POST https://graph.facebook.com/v21.0/<PHONE_NUMBER_ID>/messages
    Headers:
      Authorization: Bearer <ACCESS_TOKEN>
      Content-Type:  application/json
    Body:
      {
        "messaging_product": "whatsapp",
        "to": "94771234567",
        "type": "text",
        "text": {"body": "Your message here"}
      }

    Args:
        to_phone:  Recipient's phone number (international format, no +)
        message:   Text content to send

    Returns:
        True on success, False on failure
    """
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }

    try:
        resp = requests.post(GRAPH_API_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[Graph API] Message sent to {to_phone} ✅")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"[Graph API] HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[Graph API] Request failed: {e}")
        return False


def mark_message_read(message_id: str) -> None:
    """
    Mark an incoming message as read (shows blue ticks to the user).

    This is a best practice — it signals to the user that their message
    was received and processed.
    """
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    try:
        requests.post(GRAPH_API_URL, headers=headers, json=payload, timeout=5)
    except Exception:
        pass  # Non-critical, ignore failures


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — How Agent Kernel Replaces All of the Above
# ─────────────────────────────────────────────────────────────────────────────

AGENT_KERNEL_EQUIVALENT = """
# In production, Agent Kernel's AgentWhatsAppRequestHandler handles
# ALL of the above automatically:
#
#   from agentkernel.api import RESTAPI
#   from agentkernel.whatsapp import AgentWhatsAppRequestHandler
#
#   handler = AgentWhatsAppRequestHandler()
#   RESTAPI.run([handler], host='0.0.0.0', port=5000)
#
# AgentWhatsAppRequestHandler internally does:
#   ✅ Webhook verification   (Steps 1 above)
#   ✅ Signature validation   (Step 2 above)
#   ✅ Message parsing        (Step 3 above)
#   ✅ Reply sending          (Step 4 above)
#   ✅ Read receipts          (mark_message_read)
#   ✅ Session management     (per phone number)
#   ✅ Multi-agent routing    (Profile → Market → Recommendation)
#
# This is why we use Agent Kernel — it abstracts the Meta protocol
# complexity so we can focus on the actual AI logic.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standalone test — demonstrates the parsing logic without a real server
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Meta WhatsApp Webhook — Protocol Demonstration")
    print("=" * 60)

    # Simulate a webhook verification request
    print("\n[1] Webhook Verification (GET hub.challenge)")
    body, status = verify_webhook("subscribe", VERIFY_TOKEN, "CHALLENGE_ABC123")
    print(f"    Response: '{body}' | HTTP {status}")

    # Simulate parsing an incoming user message
    print("\n[2] Parse Incoming Message (POST from Meta)")
    sample_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"wa_id": "94771234567"}],
                    "messages": [{
                        "from": "94771234567",
                        "id": "wamid.DEMO123",
                        "type": "text",
                        "text": {"body": "under 6 million"}
                    }]
                }
            }]
        }]
    }
    parsed = parse_incoming_message(sample_payload)
    print(f"    Parsed: {parsed}")

    # Show what Agent Kernel replaces
    print("\n[3] Agent Kernel equivalent:")
    print(AGENT_KERNEL_EQUIVALENT)

    print("\n[4] Environment variables needed for live deployment:")
    for var in ["AK_WHATSAPP__VERIFY_TOKEN", "AK_WHATSAPP__ACCESS_TOKEN",
                "AK_WHATSAPP__PHONE_NUMBER_ID", "AK_WHATSAPP__API_VERSION",
                "META_APP_SECRET", "PARSE_API_KEY"]:
        val = os.environ.get(var, "(not set)")
        display = val[:8] + "..." if len(val) > 8 and val != "(not set)" else val
        print(f"    {var}: {display}")
