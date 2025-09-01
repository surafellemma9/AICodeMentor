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

# ----- Provider catalog (OpenAI-compatible /chat/completions) -----
PROVIDERS = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",  # or "deepseek-reasoner"
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
    # Optional: OpenRouter for easy switching
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

    # Native OpenAI
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "headers": lambda key, _req: {"Authorization": f"Bearer {key}"},
    },

    "gemini": {
        # We'll format the full URL with ?key= later
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
        "headers": lambda key, _req: {"Content-Type": "application/json"},  # no Bearer here
    },
}


def _to_gemini_contents(messages):
    """
    Convert OpenAI-style messages -> Gemini 'contents' list.
    We drop 'system' into an initial instruction for the user.
    """
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
            sys_prefix = ""  # only prepend once
        contents.append({
            "role": "user" if role == "user" else "model",
            "parts": [{"text": text}],
        })
    return contents


def _parse_gemini_reply(resp_json):
    """
    Pull the first text part from Gemini's response.
    """
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


def _select_provider() -> str:
    """Pick provider via env; default to openai."""
    name = os.environ.get("LLM_PROVIDER", "openai").lower()
    return name if name in PROVIDERS else "openai"


def _get_api_key(var_name: str) -> str:
    """Read API key from env/settings and strip stray whitespace/newlines/quotes."""
    raw = os.environ.get(var_name) or getattr(settings, var_name, None) or ""
    return str(raw).strip().strip('"').strip("'")


def _get_messages_from_session(request):
    """Fetch running chat transcript from session."""
    return request.session.setdefault("messages", [])


def _append_message(request, role: str, content: str):
    msgs = _get_messages_from_session(request)
    msgs.append({"role": role, "content": content})
    request.session.modified = True


def ping(_request):
    return HttpResponse("chatbot pong")


def diag(request):
    """Quick diagnostics: which provider/model and whether a key is present."""
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


# ---------- ChatGPT-style page ----------
def chat_page(request):
    messages = _get_messages_from_session(request)
    return render(request, "chatbot/form.html", {"messages": messages})


def new_chat(request):
    request.session["messages"] = []
    request.session.modified = True
    return redirect("chatbot:chatbot_home")


# ---------- Legacy simple form (optional) ----------
def form_view(request):
    return render(request, "chatbot/form.html")


# ---------- Send message to model ----------
def submit_chat(request):
    """
    Handles both:
    - Standard form POST (message in request.POST['message']) -> redirect back to chat page
    - AJAX POST with JSON body {"message": "..."} -> returns JSON {"reply_html": "..."}
    Keeps a running transcript in session for the ChatGPT-like UI.
    """
    if request.method != "POST":
        return redirect("chatbot:chatbot_home")  # make sure your urls.py names this route

    # Detect AJAX
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # Read message from POST or JSON
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

    key = _get_api_key(p["key_env"])
    if not key:
        reply = f"{provider_name} API key is missing. Set {p['key_env']} in Render → Environment."
        _append_message(request, "assistant", reply)
        if is_ajax:
            return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")})
        return redirect("chatbot:chatbot_home")

    model = (os.environ.get("LLM_MODEL") or p["default_model"]).strip()
    transcript = _get_messages_from_session(request)[-20:]
    messages_payload = [{"role": "system", "content": "You are a helpful coding mentor."}] + transcript

    provider_name = _select_provider()

    if provider_name == "gemini":
        # Build Gemini request
        base = PROVIDERS["gemini"]["url"].format(model=model)
        api_key = _get_api_key(PROVIDERS["gemini"]["key_env"])
        url = f"{base}?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": _to_gemini_contents(messages_payload),
            # Optional: safetySettings, generationConfig, tools, etc.
        }
    else:
        # OpenAI-compatible providers (deepseek, groq, together, openrouter, openai)
        url = PROVIDERS[provider_name]["url"]
        headers = PROVIDERS[provider_name]["headers"](_get_api_key(PROVIDERS[provider_name]["key_env"]), request)
        headers["Content-Type"] = "application/json"
        payload = {
            "model": model,
            "messages": messages_payload,
        }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)

        # Auth/billing handling
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

    # Add assistant reply to transcript
    _append_message(request, "assistant", reply)

    if is_ajax:
        # Return simple HTML (you can switch to Markdown->HTML if desired)
        return JsonResponse({"reply_html": escape(reply).replace("\n", "<br>")})

    # Non-AJAX: go back to the chat page which will render the transcript
    return redirect("chatbot:chatbot_home")
