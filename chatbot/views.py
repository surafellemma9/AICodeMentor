# chatbot/views.py
import json
import logging
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "openai/gpt-4o-mini"  # pick any OpenRouter-supported model

def ping(_):
    return HttpResponse("chatbot pong")

def form_view(request):
    # Renders chatbot/templates/chatbot/form.html
    return render(request, "chatbot/form.html")

def submit_chat(request):
    # Handles POST from the form; renders chatbot/response.html
    if request.method != "POST":
        return redirect("chatbot_home")

    question = (request.POST.get("message") or "").strip()
    if not question:
        return render(request, "chatbot/form.html", {"error": "Please enter a message."})

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        # Friendly message instead of a 500
        return render(request, "chatbot/response.html", {
            "question": question,
            "reply": "Server is missing OPENROUTER_API_KEY. Add it in Render → Environment."
        })

    headers = {
        "Authorization": f"Bearer {api_key}",
        # These two are recommended by OpenRouter
        "HTTP-Referer": os.environ.get("SITE_URL", "https://aicodementor.onrender.com"),
        "X-Title": "LeetAI",
    }
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a helpful coding mentor."},
            {"role": "user", "content": question},
        ],
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=45)

        # Handle common upstream auth/billing cases gracefully
        if r.status_code in (401, 403):
            return render(request, "chatbot/response.html", {
                "question": question,
                "reply": "OpenRouter API key is invalid or expired (401/403). Rotate the key and try again."
            })
        if r.status_code == 402:
            return render(request, "chatbot/response.html", {
                "question": question,
                "reply": "OpenRouter returned 402 (billing required). Check your OpenRouter billing."
            })

        if r.status_code >= 400:
            # Log body for debugging, but show a safe message to the user
            body_text = r.text[:1000]
            logger.error("OpenRouter error %s: %s", r.status_code, body_text)
            # Try to show any error message OpenRouter included
            try:
                err_json = r.json()
                err_msg = (
                    err_json.get("error", {}).get("message")
                    or err_json.get("message")
                    or body_text
                )
            except Exception:
                err_msg = body_text
            return render(request, "chatbot/response.html", {
                "question": question,
                "reply": f"Upstream error {r.status_code}: {err_msg}"
            })

        # Success: parse reply robustly
        data = r.json()
        choice0 = (data.get("choices") or [{}])[0]
        reply = (choice0.get("message") or {}).get("content") or choice0.get("text") or ""
        reply = reply.strip() or "The model returned an empty reply."

    except requests.Timeout:
        reply = "The model request timed out. Please try again."
    except Exception as e:
        # Log full stack to Render logs, but show a friendly message
        logger.exception("submit_chat failed")
        reply = f"Unexpected error contacting model: {e}"

    return render(request, "chatbot/response.html", {"question": question, "reply": reply})
