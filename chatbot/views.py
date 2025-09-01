# chatbot/views.py
import json
import logging
import os
import uuid

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import escape

logger = logging.getLogger(__name__)

# ----- Provider catalog (OpenAI-compatible /chat/completions) -----
PROVIDERS = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "default_model": "llama-3.1-70b-versatile",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
    },
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "key_env": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
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
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
        "headers": lambda key, _req: {"Content-Type": "application/json"},
    },
}

# --------- Gemini adapters ----------
def _to_gemini_contents(messages):
    contents = []
    system_texts = [m["content"] for m in messages if m.get("role") == "system"]
    sys_prefix = ("\n".join(system_texts) + "\n") if system_texts else ""
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role not in ("user", "assistant"):
            continue
        text = m.get("content", "")
        if role == "user" and sys_prefix:
            text = sys_prefix + text
            sys_prefix = ""
        contents.append({"role": "user" if role == "user" else "model", "parts": [{"text": text}]})
    return contents

def _parse_gemini_reply(resp_json):
    try:
        cands = resp_json.get("candidates") or []
        if not cands:
            return ""
        parts = ((cands[0].get("content") or {}).get("parts") or [])
        for p in parts:
            if "text" in p:
                return p["text"]
        return ""
    except Exception:
        return ""

# --------- Provider selection ----------
def _select_provider() -> str:
    name = os.environ.get("LLM_PROVIDER", "openai").lower()
    return name if name in PROVIDERS else "openai"

def _get_api_key(var_name: str) -> str:
    raw = os.environ.get(var_name) or getattr(settings, var_name, None) or ""
    return str(raw).strip().strip('"').strip("'")

# --------- Conversation helpers (session) ----------
def _ensure_conversations(request):
    """Ensure session has a conversations list and a current ID.
       Migrate old 'messages' if present."""
    convos = request.session.get("conversations")
    if not convos:
        convos = []
        old = request.session.get("messages", [])
        cid = uuid.uuid4().hex
        convos.append({"id": cid, "title": "New conversation", "messages": old})
        request.session["conversations"] = convos
        request.session["current_convo_id"] = cid
        request.session.modified = True
    if not request.session.get("current_convo_id"):
        request.session["current_convo_id"] = convos[0]["id"]
        request.session.modified = True
    return convos

def _get_conversations_list(request):
    return [{"id": c["id"], "title": c.get("title") or "New conversation"} for c in _ensure_conversations(request)]

def _current_convo(request):
    convos = _ensure_conversations(request)
    cid = request.session.get("current_convo_id")
    for c in convos:
        if c["id"] == cid:
            return c
    request.session["current_convo_id"] = convos[0]["id"]
    request.session.modified = True
    return convos[0]

def _set_current_convo(request, convo_id: str):
    convos = _ensure_conversations(request)
    for c in convos:
        if c["id"] == convo_id:
            request.session["current_convo_id"] = convo_id
            request.session.modified = True
            return c
    return _current_convo(request)

def _new_convo(request):
    convos = _ensure_conversations(request)
    cid = uuid.uuid4().hex
    convo = {"id": cid, "title": "New conversation", "messages": []}
    convos.append(convo)
    request.session["current_convo_id"] = cid
    request.session.modified = True
    return convo

def _append_current_message(request, role: str, content: str):
    convo = _current_convo(request)
    convo["messages"].append({"role": role, "content": content})
    request.session.modified = True

def _maybe_set_title_from_first_user_msg(convo):
    if convo.get("title") and convo["title"] != "New conversation":
        return
    # first non-empty user message -> title
    for m in convo["messages"]:
        if m.get("role") == "user":
            text = " ".join(m.get("content", "").split())
            if text:
                title = text[:60]
                convo["title"] = title
                return

# --------- Simple views ----------
def ping(_request):
    return HttpResponse("chatbot pong")

def diag(request):
    name = _select_provider()
    p = PROVIDERS[name]
    key_ok = bool(_get_api_key(p["key_env"]))
    return JsonResponse({"provider": name, "model": os.environ.get("LLM_MODEL", p["default_model"]), "has_api_key": key_ok})

# ---------- Pages ----------
def chat_page(request, convo_id: str | None = None):
    if convo_id:
        _set_current_convo(request, convo_id)
    convo = _current_convo(request)
    return render(
        request,
        "chatbot/form.html",
        {
            "messages": convo["messages"],
            "conversations": _get_conversations_list(request),
            "current_id": convo["id"],
        },
    )

def new_chat(request):
    convo = _new_convo(request)
    return redirect("chatbot:chatbot_chat", convo_id=convo["id"])

# ---------- Legacy simple form (optional) ----------
def form_view(request):
    return render(request, "chatbot/form.html")

# ---------- Send message to model ----------
def submit_chat(request):
    if request.method != "POST":
        return redirect("chatbot:chatbot_home")

    # AJAX?
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
        msg = "Please enter a message."
        _append_current_message(request, "assistant", msg)
        if is_ajax:
            return JsonResponse({"error": msg}, status=400)
        return redirect("chatbot:chatbot_home")

    # Append user message
    _append_current_message(request, "user", question)
    convo = _current_convo(request)
    _maybe_set_title_from_first_user_msg(convo)

    provider_name = _select_provider()
    p = PROVIDERS[provider_name]

    key = _get_api_key(p["key_env"])
    if not key:
        reply = f"{provider_name} API key is missing. Set {p['key_env']} in Render → Environment."
        _append_current_message(request, "assistant", reply)
        if is_ajax:
            return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")})
        return redirect("chatbot:chatbot_home")

    model = (os.environ.get("LLM_MODEL") or p["default_model"]).strip()

    transcript = convo["messages"][-20:]
    messages_payload = [{"role": "system", "content": "You are a helpful coding mentor."}] + transcript

    if provider_name == "gemini":
        base = PROVIDERS["gemini"]["url"].format(model=model)
        api_key = _get_api_key(PROVIDERS["gemini"]["key_env"])
        url = f"{base}?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": _to_gemini_contents(messages_payload)}
    else:
        url = PROVIDERS[provider_name]["url"]
        headers = PROVIDERS[provider_name]["headers"](_get_api_key(PROVIDERS[provider_name]["key_env"]), request)
        headers["Content-Type"] = "application/json"
        payload = {"model": model, "messages": messages_payload}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)

        if r.status_code in (401, 403):
            reply = f"{provider_name} rejected the key (HTTP {r.status_code}). Verify the key and referer/domain settings."
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
            if provider_name == "gemini":
                reply = _parse_gemini_reply(data).strip() or "The model returned an empty reply."
            else:
                choice0 = (data.get("choices") or [{}])[0]
                reply = (choice0.get("message") or {}).get("content") or choice0.get("text") or ""
                reply = (reply or "").strip() or "The model returned an empty reply."

    except requests.Timeout:
        reply = "The model request timed out. Please try again."
    except Exception:
        logger.exception("submit_chat failed (provider=%s)", provider_name)
        reply = "Unexpected error contacting model. Please try again."

    _append_current_message(request, "assistant", reply)

    if is_ajax:
        return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")})
    return redirect("chatbot:chatbot_home")
