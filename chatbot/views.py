import logging
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

# ----- Provider catalog (OpenAI-compatible chat/completions) -----
PROVIDERS = {
    # Current provider you used
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4o-mini",
        "headers": lambda key, request: {
            "Authorization": f"Bearer {key}",
            # These two are recommended by OpenRouter
            "HTTP-Referer": (request.build_absolute_uri("/") if request else settings.SITE_URL),
            "X-Title": "LeetAI",
        },
    },
    # Popular free/cheap option; usually OpenAI-compatible
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        # Good default model name on Groq:
        "default_model": "llama-3.1-70b-versatile",
        "headers": lambda key, _request: {"Authorization": f"Bearer {key}"},
    },
    # Another OpenAI-compatible option
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "key_env": "TOGETHER_API_KEY",
        # Example fast instruct model on Together (adjust as you like)
        "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "headers": lambda key, _request: {"Authorization": f"Bearer {key}"},
    },
}

# Choose provider via env var (LLM_PROVIDER=openrouter|groq|together)
def _select_provider():
    name = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    return name if name in PROVIDERS else "openrouter"

def ping(_):
    return HttpResponse("chatbot pong")

def form_view(request):
    return render(request, "chatbot/form.html")

def submit_chat(request):
    if request.method != "POST":
        return redirect("chatbot_home")

    question = (request.POST.get("message") or "").strip()
    if not question:
        return render(request, "chatbot/form.html", {"error": "Please enter a message."})

    provider_name = _select_provider()
    p = PROVIDERS[provider_name]
    key = os.environ.get(p["key_env"]) or getattr(settings, p["key_env"], None)

    if not key:
        return render(
            request,
            "chatbot/response.html",
            {
                "question": question,
                "reply": (
                    f"{provider_name} API key is missing. "
                    f"Set {p['key_env']} in Render → Environment."
                ),
            },
        )

    url = p["url"]
    headers = p["headers"](key, request)
    model = os.environ.get("LLM_MODEL", p["default_model"])

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful coding mentor."},
            {"role": "user", "content": question},
        ],
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)

        # Friendly auth/billing messages (codes vary across providers)
        if r.status_code in (401, 403):
            return render(
                request,
                "chatbot/response.html",
                {
                    "question": question,
                    "reply": (
                        f"{provider_name} rejected the key (HTTP {r.status_code}). "
                        f"Verify the key and any domain/referrer settings."
                    ),
                },
            )
        if r.status_code == 402:
            return render(
                request,
                "chatbot/response.html",
                {
                    "question": question,
                    "reply": f"{provider_name} returned 402 (billing required).",
                },
            )

        if r.status_code >= 400:
            # Log details for debugging; show concise message to user
            body = r.text[:1200]
            logger.error("%s error %s: %s", provider_name, r.status_code, body)
            # Try to pull a message if JSON
            try:
                msg = (r.json().get("error") or {}).get("message") or r.json().get("message") or body
            except Exception:
                msg = body
            return render(
                request,
                "chatbot/response.html",
                {"question": question, "reply": f"Upstream error {r.status_code}: {msg}"},
            )

        data = r.json()
        # OpenAI-compatible: choices[0].message.content or choices[0].text
        choice0 = (data.get("choices") or [{}])[0]
        reply = (choice0.get("message") or {}).get("content") or choice0.get("text") or ""
        reply = reply.strip() or "The model returned an empty reply."

    except requests.Timeout:
        reply = "The model request timed out. Please try again."
    except Exception as e:
        logger.exception("submit_chat failed")
        reply = f"Unexpected error contacting model: {e}"

    return render(request, "chatbot/response.html", {"question": question, "reply": reply})
