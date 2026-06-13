import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import httpx
import json

BACKEND_URL = os.getenv("BACKEND_URL", "https://support-copilot-backend.onrender.com")

SAMPLE_TICKETS = [
    # Billing
    {
        "user_query": "I was charged twice for my order. Please help.",
        "agent_response": "I'm sorry for the inconvenience! I can see a duplicate charge on your account. I've initiated a refund for the extra charge — it will reflect in your account within 3–5 business days. Please share your transaction ID for confirmation.",
        "category": "billing",
    },
    {
        "user_query": "My payment failed but money was deducted from my account.",
        "agent_response": "This can happen due to a network issue during payment processing. The amount will be automatically refunded within 5–7 business days. If it doesn't reflect after that, please contact your bank with transaction reference number.",
        "category": "billing",
    },
    {
        "user_query": "How do I get a refund for my cancelled order?",
        "agent_response": "Refunds for cancelled orders are processed within 3–5 business days to your original payment method. You'll receive a confirmation email once processed. If you paid via COD, please provide your bank details for a direct transfer.",
        "category": "billing",
    },
    # Account
    {
        "user_query": "I forgot my password and can't log in.",
        "agent_response": "No worries! Click 'Forgot Password' on the login page and enter your registered email. You'll receive a reset link within 2 minutes. Check your spam folder if you don't see it. The link expires in 24 hours.",
        "category": "account",
    },
    {
        "user_query": "My account has been locked. How do I unlock it?",
        "agent_response": "Accounts are locked after 5 failed login attempts for security. Please wait 30 minutes and try again, or use the 'Forgot Password' option to reset your credentials immediately.",
        "category": "account",
    },
    {
        "user_query": "How do I change my registered email address?",
        "agent_response": "To change your email, go to Account Settings → Personal Info → Edit Email. You'll need to verify your new email address via a confirmation link. This change may take up to 1 hour to reflect.",
        "category": "account",
    },
    # Shipping
    {
        "user_query": "My order hasn't arrived yet. It's been 10 days.",
        "agent_response": "I apologize for the delay! I've checked your order and it's currently at the dispatch hub. Estimated delivery is within the next 2 days. I've also raised a priority flag on your shipment. You'll receive tracking updates via SMS.",
        "category": "shipping",
    },
    {
        "user_query": "Can I change my delivery address after placing the order?",
        "agent_response": "Address changes are possible only within 1 hour of placing the order. After that, the order enters processing and cannot be modified. Please contact us immediately at support@company.com if you're within that window.",
        "category": "shipping",
    },
    {
        "user_query": "I received the wrong item in my order.",
        "agent_response": "I sincerely apologize for this error! Please take a photo of the wrong item received and share it with us. We'll arrange a free pickup and send the correct item within 2–3 business days at no extra cost.",
        "category": "shipping",
    },
    # Technical
    {
        "user_query": "The app keeps crashing when I try to checkout.",
        "agent_response": "Try clearing the app cache (Settings → Apps → Clear Cache) and restart the app. If the issue persists, try uninstalling and reinstalling the latest version. Our team is also aware of a checkout bug in v3.2 and a fix is rolling out in 24 hours.",
        "category": "technical",
    },
    {
        "user_query": "I can't upload my profile picture. It keeps failing.",
        "agent_response": "Profile pictures must be JPG/PNG format and under 5MB. If your image meets these requirements, try using a different browser or clearing cache. If still failing, our engineering team has a known issue logged and it should be fixed within 48 hours.",
        "category": "technical",
    },
]


def seed():
    print(f"Seeding {len(SAMPLE_TICKETS)} tickets to {BACKEND_URL}/ingest/bulk ...")
    response = httpx.post(
        f"{BACKEND_URL}/ingest/bulk",
        json=SAMPLE_TICKETS,
        timeout=120.0,
    )
    result = response.json()
    print(f"✅ Inserted: {result['inserted']}")
    print(f"❌ Failed:   {result['failed']}")
    if result["errors"]:
        print("Errors:", json.dumps(result["errors"], indent=2))
    print("Done! Your RAG system is ready.")


if __name__ == "__main__":
    seed()