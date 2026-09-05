"""Webhook signature verification service."""

import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify Razorpay webhook signature using HMAC-SHA256.

    Args:
        raw_body: Raw request body bytes (must be unparsed)
        signature: X-Razorpay-Signature header value
        secret: Webhook secret from RAZORPAY_WEBHOOK_SECRET environment variable

    Returns:
        True if signature is valid, False otherwise
    """
    if not secret:
        logger.error("Webhook secret not configured")
        return False

    if not signature:
        logger.warning("Missing X-Razorpay-Signature header")
        return False

    # Compute expected signature using HMAC-SHA256
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)


def get_webhook_secret() -> str:
    """
    Get webhook secret from environment.

    Returns:
        Webhook secret string

    Raises:
        RuntimeError: If secret is not configured
    """
    import os
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("RAZORPAY_WEBHOOK_SECRET environment variable not set")
    return secret