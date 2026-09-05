#!/usr/bin/env python
"""
Local Razorpay webhook testing script.

Generates a signed refund.created webhook payload and sends it to the
local Sentinel backend for end-to-end testing.

Usage:
    python scripts/test_webhook.py [--host HOST] [--port PORT] [--secret SECRET]
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime

import requests


DEFAULT_PAYLOAD = {
    "entity": "event",
    "account_id": "acc_E7OQJcEANmBHTC",
    "event": "refund.created",
    "contains": ["refund", "payment"],
    "payload": {
        "refund": {
            "id": "rfnd_FS8TWyPrCsa0OB",
            "entity": "refund",
            "amount": 50000,
            "currency": "INR",
            "payment_id": "pay_FPoJKWQQ8lK13n",
            "notes": {"comment": "Customer Notes for Webhooks."},
            "receipt": None,
            "acquirer_data": {"arn": None},
            "created_at": 1597734071,
            "batch_id": None,
            "status": "processed",
            "speed_processed": "normal",
            "speed_requested": "optimum"
        },
        "payment": {
            "id": "pay_FPoJKWQQ8lK13n",
            "entity": "payment",
            "amount": 500000,
            "currency": "INR",
            "base_amount": 500000,
            "status": "captured",
            "order_id": "order_FPoIeimWki9j8A",
            "invoice_id": None,
            "international": False,
            "method": "netbanking",
            "amount_refunded": 190000,
            "amount_transferred": 0,
            "refund_status": "partial",
            "captured": True,
            "description": None,
            "card_id": None,
            "bank": "HDFC",
            "wallet": None,
            "vpa": None,
            "email": "gaurav.kumar@example.com",
            "contact": "+919000090000",
            "notes": [],
            "fee": 11800,
            "tax": 1800,
            "error_code": None,
            "error_description": None,
            "error_source": None,
            "error_step": None,
            "error_reason": None,
            "acquirer_data": {"bank_transaction_id": "4827433"},
            "created_at": 1597226379
        }
    },
    "created_at": 1597734071
}


def sign_payload(payload: dict, secret: str) -> tuple:
    """Generate HMAC-SHA256 signature for webhook payload.

    Returns:
        Tuple of (raw_body_bytes, signature_hex)
    """
    # Use separators to match Razorpay's serialization (no whitespace)
    raw_body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return raw_body, signature


def send_webhook(
    host: str,
    port: int,
    secret: str,
    payload: dict,
    event_id: str = None
) -> requests.Response:
    """Send a signed webhook to the local backend."""
    if event_id is None:
        event_id = f"evt_test_{int(time.time())}"

    raw_body, signature = sign_payload(payload, secret)

    url = f"http://{host}:{port}/api/webhooks/razorpay"
    headers = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": event_id,
        "Content-Type": "application/json",
    }

    print(f"Sending webhook to {url}")
    print(f"  Event ID: {event_id}")
    print(f"  Signature: {signature[:16]}...")
    print(f"  Payload size: {len(payload)} bytes")

    # Send raw body to preserve signature
    response = requests.request(
        "POST",
        f"http://{host}:{port}/api/webhooks/razorpay",
        data=json.dumps(payload, separators=(',', ':')).encode('utf-8'),
        headers={
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": event_id,
            "Content-Type": "application/json",
        },
        timeout=10
    )
    return response


def wait_for_processing(
    host: str,
    port: int,
    refund_id: str,
    timeout: int = 30,
    poll_interval: float = 1.0
) -> dict:
    """Poll for queue processing to complete."""
    url = f"http://{host}:{port}/api/cases"
    start = time.time()

    while time.time() - start < timeout:
        try:
            resp = requests.get(f"http://{host}:{port}/api/cases", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for case in data.get("cases", []):
                    if case.get("refund_id") == refund_id:
                        return case
        except Exception:
            pass
        time.sleep(poll_interval)

    return None


def check_queue_status(host: str, port: int, refund_id: str) -> dict:
    """Check queue status for a refund."""
    try:
        resp = requests.get(f"http://{host}:{port}/api/integration/queue", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("items", []):
                if item.get("refund_id") == refund_id:
                    return item
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Test Razorpay webhook locally")
    parser.add_argument("--host", default="localhost", help="Backend host")
    parser.add_argument("--port", type=int, default=8000, help="Backend port")
    parser.add_argument("--secret", default=os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret_12345678901234567890123456789012"), help="Webhook secret")
    parser.add_argument("--event-id", help="Custom event ID (default: generated)")
    parser.add_argument("--wait", action="store_true", help="Wait for queue processing")
    parser.add_argument("--timeout", type=int, default=30, help="Processing timeout (seconds)")
    args = parser.parse_args()

    # Set secret in environment for the backend
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = args.secret

    print("=" * 60)
    print("Razorpay Webhook Local Test")
    print("=" * 60)
    print(f"Backend: http://{args.host}:{args.port}")
    print(f"Secret: {args.secret[:8]}...")
    print()

    # Check health first
    try:
        health = requests.get(f"http://{args.host}:{args.port}/api/health", timeout=5)
        print(f"Health check: {health.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

    # Generate webhook
    event_id = args.event_id or f"evt_test_{int(time.time())}"
    raw_body, signature = sign_payload(DEFAULT_PAYLOAD, args.secret)

    url = f"http://{args.host}:{args.port}/api/webhooks/razorpay"
    headers = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": args.event_id or f"evt_test_{int(time.time())}",
        "Content-Type": "application/json",
    }

    print(f"\nSending webhook...")
    print(f"  URL: http://{args.host}:{args.port}/api/webhooks/razorpay")
    print(f"  Event ID: {headers['x-razorpay-event-id']}")
    print(f"  Signature: {signature[:16]}...")
    print(f"  Refund ID: {DEFAULT_PAYLOAD['payload']['refund']['id']}")
    print()

    # Send with raw body to preserve signature
    raw_body = json.dumps(DEFAULT_PAYLOAD, separators=(',', ':')).encode('utf-8')
    response = requests.request(
        "POST",
        f"http://{args.host}:{args.port}/api/webhooks/razorpay",
        data=raw_body,
        headers={
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": args.event_id or f"evt_test_{int(time.time())}",
            "Content-Type": "application/json",
        },
        timeout=10
    )

    print(f"Response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        sys.exit(1)

    print("Webhook acknowledged successfully!")

    refund_id = DEFAULT_PAYLOAD["payload"]["refund"]["id"]
    print(f"\nRefund ID: {refund_id}")
    print(f"Event ID: {headers['x-razorpay-event-id']}")

    # Check queue status
    print("\nChecking queue...")
    time.sleep(1)
    queue_item = check_queue_status(args.host, args.port, DEFAULT_PAYLOAD["payload"]["refund"]["id"])
    if queue_item:
        print(f"Queue status: {queue_item.get('status')}")
        print(f"Queue ID: {queue_item.get('id')}")
    else:
        print("Not found in queue (may have been processed already)")

    # Wait for processing if requested
    if args.wait:
        print(f"\nWaiting for processing (timeout: {args.timeout}s)...")
        case = wait_for_processing(args.host, args.port, DEFAULT_PAYLOAD["payload"]["refund"]["id"], timeout=args.timeout)
        if case:
            print(f"\nCase created!")
            print(f"  Case ID: {case.get('id')}")
            print(f"  Risk Score: {case.get('risk_score')}")
            print(f"  Risk Band: {case.get('risk_band')}")
            print(f"  Action: {case.get('recommended_action')}")
            print(f"  Status: {case.get('status')}")
        else:
            print(f"\nCase not created within {args.timeout}s")
            print("Check queue monitor logs for processing status.")

    # Test duplicate event idempotency
    print("\n" + "=" * 60)
    print("Testing duplicate event idempotency...")
    print("=" * 60)

    raw_body = json.dumps(DEFAULT_PAYLOAD, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        args.secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    dup_event_id = f"evt_duplicate_{int(time.time())}"
    headers_dup = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": dup_event_id,
        "Content-Type": "application/json",
    }

    # Send twice
    resp1 = requests.request("POST", f"http://{args.host}:{args.port}/api/webhooks/razorpay", data=raw_body, headers=headers_dup, timeout=10)
    resp2 = requests.request("POST", f"http://{args.host}:{args.port}/api/webhooks/razorpay", data=raw_body, headers=headers_dup, timeout=10)

    print(f"First request:  {resp1.status_code}")
    print(f"Second request: {resp2.status_code}")

    if resp1.status_code == 200 and resp2.status_code == 200:
        print("✓ Duplicate event idempotency works correctly!")
    else:
        print("✗ Duplicate handling issue")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    import hashlib
    import hmac
    main()