# chatbot/views.py
import json
import logging
import os

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import escape

logger = logging.getLogger(__name__)

# ----- Provider catalog -----
# Add "kind" so we know which payload/URL style to use.
PROVIDERS = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
        "kind": "openai",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "default_model": "llama-3.1-70b-versatile",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
        "kind": "openai",
    },
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "key_env": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
        "kind": "openai",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4o-mini",
        "headers": lambda key, req: {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": (req.build_absolute_uri("/") if req else getattr(settings, "SITE_URL", "")),
            "X-Title": "LeetAI",
        },
        "kind": "openai",
    },
    # ---- NEW: Google Gemini (Generative Language API) ----
    "gemini": {
        # We will append ?key=API_KEY at request time
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
        # Gemini expects JSON content-type; no Authorization header
        "headers": lambda _key, _req: {"Content-Type": "application/json"},
        "kind": "gemini",
    },
}


def _select_provider() -> str:
    name = os.environ.get("LLM_PROVIDER", "deepseek").lower()
    return name if name in PROVIDERS else "deepseek"


def _get_api_key(var_name: str) -> str:
    raw = os.environ.get(var_name) or getattr(settings, var_name, None) or ""
    return str(raw).strip().strip('"').strip("'")


def _get_messages_from_session(request):
    return request.session.setdefault("messages", [])


def _append_message(request, role: str, content: str):
    msgs = _get_messages_from_session(request)
    msgs.append({"role": role, "content": content})
    request.session.modified = True


def ping(_request):
    return HttpResponse("chatbot pong")


def diag(request):
    name = _select_provider()
    p = PROVIDERS[name]
    key_ok = bool(_get_api_key(p["key_env"]))
    return JsonResponse(
        {
            "provider": name,
            "model": os.environ.get("LLM_MODEL", p["default_model"]),
            "has_api_key": key_ok,
        }
    )


# ---------- Chat page (ChatGPT-like) ----------
def chat_page(request):
    messages = request.session.setdefault("messages", [])
    return render(request, "chatbot/form.html", {"messages": messages})



def new_chat(request):
    request.session["messages"] = []
    request.session.modified = True
    return redirect("chatbot:chatbot_home")


# ---------- Simple form (legacy/optional) ----------
def form_view(request):
    return render(request, "chatbot/form.html")


# ---------- Minimal Gemini probe (debug) ----------
def gemini_probe(_request):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gemini-1.5-flash").strip()
    if not api_key:
        return JsonResponse({"ok": False, "why": "Missing GEMINI_API_KEY"}, status=500)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": "Say 'pong' if you can hear me."}]}]}
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        content_type = r.headers.get("content-type", "")
        out = r.json() if content_type.startswith("application/json") else r.text
        return JsonResponse({"ok": r.ok, "status": r.status_code, "json": out}, status=r.status_code)
    except Exception as e:
        return JsonResponse({"ok": False, "why": str(e)}, status=500)


# ---------- Main submit ----------
def submit_chat(request):
    """
    Supports:
      - Form POST (message in request.POST['message']) -> redirect back to chat page
      - AJAX POST (JSON {"message": ...}) -> JSON {"reply_html": "..."}
    """
    if request.method != "POST":
        return redirect("chatbot:chatbot_home")

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # Read message
    question = ""
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8"))
            question = (payload.get("message") or "").strip()
        except Exception:
            question = ""
    if not question:
        question = (request.POST.get("message") or "").strip()

    if not question:
        if is_ajax:
            return JsonResponse({"error": "Please enter a message."}, status=400)
        _append_message(request, "assistant", "Please enter a message.")
        return redirect("chatbot:chatbot_home")

    # Add user message to transcript
    _append_message(request, "user", question)

    provider_name = _select_provider()
    p = PROVIDERS[provider_name]
    model = (os.environ.get("LLM_MODEL") or p["default_model"]).strip()

    key = _get_api_key(p["key_env"])
    if not key:
        reply = f"{provider_name} API key is missing. Set {p['key_env']} in Render → Environment."
        _append_message(request, "assistant", reply)
        return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")}) if is_ajax else redirect("chatbot:chatbot_home")

    try:
        if p["kind"] == "openai":
            url = p["url"]
            headers = p["headers"](key, request)
            headers["Content-Type"] = "application/json"

            transcript = _get_messages_from_session(request)[-20:]
            messages_payload = [{"role": "system", "content": "You are a helpful coding mentor."}] + transcript
            payload = {"model": model, "messages": messages_payload}
            r = requests.post(url, headers=headers, json=payload, timeout=60)

        elif p["kind"] == "gemini":
            # Gemini: key in query string, payload uses 'contents'
            base = p["url"].format(model=model)
            url = f"{base}?key={key}"
            headers = p["headers"](key, request)  # sets content-type
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": question}]}
                ]
            }
            r = requests.post(url, headers=headers, json=payload, timeout=60)

        else:
            return _finalize_reply(request, is_ajax, "Unknown provider kind.")

        # Handle HTTP errors uniformly
        if r.status_code in (401, 403):
            reply = f"{provider_name} rejected the key (HTTP {r.status_code}). Verify the key and access."
        elif r.status_code == 402:
            reply = f"{provider_name} returned 402 (billing required)."
        elif r.status_code >= 400:
            body = r.text[:1200]
            logger.error("%s error %s: %s", provider_name, r.status_code, body)
            try:
                j = r.json()
                msg = (j.get("error") or {}).get("message") or j.get("message") or body
            except Exception:
                msg = body
            reply = f"Upstream error {r.status_code}: {msg}"
        else:
            data = r.json()
            if p["kind"] == "openai":
                choice0 = (data.get("choices") or [{}])[0]
                reply = (choice0.get("message") or {}).get("content") or choice0.get("text") or ""
            else:  # gemini
                cands = data.get("candidates") or []
                parts = (cands[0].get("content") or {}).get("parts") if cands else []
                texts = [part.get("text", "") for part in (parts or [])]
                reply = "\n".join([t for t in texts if t]).strip()
            reply = reply or "The model returned an empty reply."

    except requests.Timeout:
        reply = "The model request timed out. Please try again."
    except Exception:
        logger.exception("submit_chat failed (provider=%s)", provider_name)
        reply = "Unexpected error contacting model. Please try again."

    _append_message(request, "assistant", reply)
    return _finalize_reply(request, is_ajax, reply)


def _finalize_reply(request, is_ajax: bool, reply: str):
    if is_ajax:
        return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")})
    return redirect("chatbot:chatbot_home")
