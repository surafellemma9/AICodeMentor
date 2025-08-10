import json
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render


def form_view(request):
    return render(request, "chatbot/form.html")

def ping(_request):
    return HttpResponse("chatbot pong")

def submit_chat(request):
    if request.method != "POST":
        return redirect("chatbot_home")

    question = (request.POST.get("message") or "").strip()
    if not question:
        return render(request, "chatbot/form.html", {"error": "Please enter a message."})

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return render(request, "chatbot/response.html",
                    {"question": question, "reply": "Server is missing OPENROUTER_API_KEY."})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.environ.get("SITE_URL", "https://aicodementor.onrender.com"),
        "X-Title": "LeetAI",
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful coding mentor."},
            {"role": "user", "content": question},
        ],
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers=headers, json=payload, timeout=60)
        if r.status_code in (401, 403):
            return render(request, "chatbot/response.html",
                        {"question": question, "reply": "OpenRouter API key is invalid or expired."})
        if r.status_code == 402:
            return render(request, "chatbot/response.html",
                        {"question": question, "reply": "Billing required on OpenRouter (402)."})
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Error contacting model: {e}"

    return render(request, "chatbot/response.html", {"question": question, "reply": reply})
