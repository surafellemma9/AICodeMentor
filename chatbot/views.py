import json
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render


def ping(_):
    return HttpResponse("chatbot pong")

def form_view(request):
    # Renders your existing template at chatbot/templates/chatbot/form.html
    return render(request, "chatbot/form.html")

def submit_chat(request):
    # Handles the form POST; renders chatbot/response.html
    if request.method != "POST":
        return redirect("chatbot_home")

    question = (request.POST.get("message") or "").strip()
    if not question:
        return render(request, "chatbot/form.html", {"error": "Please enter a message."})

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return render(request, "chatbot/response.html", {
            "question": question,
            "reply": "Server is missing OPENROUTER_API_KEY."
        })

    headers = {
        "Authorization": f"Bearer {api_key}",
        # These two headers are recommended by OpenRouter
        "HTTP-Referer": os.environ.get("SITE_URL", "https://aicodementor.onrender.com"),
        "X-Title": "LeetAI",
    }
    payload = {
        "model": "openai/gpt-4o-mini",   # pick any OpenRouter-supported model
        "messages": [
            {"role": "system", "content": "You are a helpful coding mentor."},
            {"role": "user", "content": question},
        ],
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Error contacting model: {e}"

    return render(request, "chatbot/response.html", {"question": question, "reply": reply})
