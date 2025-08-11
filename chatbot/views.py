import json
import logging
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "openai/gpt-4o-mini"  # choose any OpenRouter-supported model

def ping(_request):
    return HttpResponse("chatbot pong")

def form_view(request):
    # Renders chatbot/templates/chatbot/form.html
    return render(request, "chatbot/form.html")

def submit_chat(request):
    # Handles POST and renders chatbot/response.html
    if request.method != "POST":
        return redirect("chatbot_home")

    question = (request.POST.get("message") or "").strip()
    if not question:
        return render(request, "chatbot/form.html", {"error": "Please enter a message."})

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return render(request, "chatbot/response.html", {
            "question": question,
            "reply": "Server is missing OPENROUTER_API_KEY. Add it in Render → Environment."
        })

    # Build a safe referer (avoid reversing any non-existent route names)
    referer = request.build_absolute_uri("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": referer,         # recommended by OpenRouter
        "X-Title": "LeetAI",             # recommended by OpenRouter
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
            body_text = r.text[:1000]
            logger.error("OpenRouter error %s: %s", r.status_code, body_text)
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

        data = r.json()
        choice0 = (data.get("choices") or [{}])[0]
        reply = (choice0.get("message") or {}).get("content") or choice0.get("text") or ""
        reply = reply.strip() or "The model returned an empty reply."

    except requests.Timeout:
        reply = "The model request timed out. Please try again."
    except Exception as e:
        logger.exception("submit_chat failed")
        reply = f"Unexpected error contacting model: {e}"

    return render(request, "chatbot/response.html", {"question": question, "reply": reply})
