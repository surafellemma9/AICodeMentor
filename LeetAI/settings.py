# LeetAI/settings.py
import os
from pathlib import Path

# Optional: database URL helper (works if installed)
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# Core / Security
# ------------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-only")
# On Render we set env var RENDER=true; that turns DEBUG off in prod.
DEBUG = "RENDER" not in os.environ

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF needs full scheme+host entries (no wildcards)
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# ------------------------------------------------------------------------------
# Apps / Middleware
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",

    # Tailwind integration (safe before theme exists)
    "tailwind",
    # DO NOT add "theme" yet — run `manage.py tailwind init` first, then add it.
    "theme",

    # Important: put this BEFORE 'django.contrib.staticfiles'
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    # your app
    "chatbot",
]

# Tailwind settings
TAILWIND_APP_NAME = "theme"
# If npm isn't found automatically, set this path (Mac Homebrew default shown)
# NPM_BIN_PATH = "/opt/homebrew/bin/npm"  # or "/usr/local/bin/npm" on Intel Macs

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be right after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "LeetAI.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # project-level templates
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # loads app templates at app/templates/<app>/*
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "LeetAI.wsgi.application"

# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # fine for simple deploys
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# If DATABASE_URL is provided (e.g., Render PostgreSQL), use it:
if dj_database_url:
    cfg = dj_database_url.config(conn_max_age=600, ssl_require=True)
    if cfg:
        DATABASES["default"].update(cfg)

# ------------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# Static files (WhiteNoise)
# ------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only include static folders that exist to avoid W004 warnings on Render
static_candidates = [BASE_DIR / "static", BASE_DIR / "chatbot" / "static"]
STATICFILES_DIRS = [p for p in static_candidates if p.exists()]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# Production security toggles
# ------------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Optional HSTS (enable once you’re confident)
    # SECURE_HSTS_SECONDS = 3600
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

# ------------------------------------------------------------------------------
# App-specific / LLM provider settings (env-driven)
# ------------------------------------------------------------------------------
SITE_URL = os.environ.get(
    "SITE_URL",
    f"https://{RENDER_EXTERNAL_HOSTNAME}" if RENDER_EXTERNAL_HOSTNAME else "http://localhost:8000",
)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-4o-mini")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# ------------------------------------------------------------------------------
# Logging (surface errors in Render logs)
# ------------------------------------------------------------------------------
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": True},
        "chatbot": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": True},
    },
}
