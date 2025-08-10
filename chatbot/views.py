# chatbot/views.py (example)
import json
import os

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def chat(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    data = json.loads(request.body.decode())
    user_msg = data.get("message")
    if not user_msg:
        return HttpResponseBadRequest("Missing 'message'")

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return JsonResponse({"error": "Missing OPENROUTER_API_KEY"}, status=500)

    headers = {
        "Authorization": f"Bearer {api_key}",
        # OpenRouter recommends these two for rate‑limit friendliness/attribution:
        "HTTP-Referer": os.environ.get("SITE_URL", "https://aicodementor.onrender.com"),
        "X-Title": "LeetAI",
    }
    payload = {
        "model": "openai/gpt-4o-mini",  # pick any OpenRouter-supported model
        "messages": [
            {"role": "system", "content": "You are a helpful coding mentor."},
            {"role": "user", "content": user_msg},
        ],
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    return JsonResponse({"reply": content})
