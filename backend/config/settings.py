"""Cấu hình Django cho backend IoT Room.

Mọi giá trị thay đổi theo máy (mật khẩu, địa chỉ) đọc từ file `.env` — xem `.env.example`.
Các lựa chọn "không được đổi" đều có ghi chú trỏ về tài liệu thiết kế.
"""
from pathlib import Path

from decouple import Csv, config as env

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())


# ---------------------------------------------------------------------------
# Ứng dụng
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "daphne",                        # phải đứng đầu: `runserver` chạy bằng ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Thư viện ngoài
    "rest_framework",
    "rest_framework.authtoken",      # bảng authtoken_token — 05-API.md §2.2
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "channels",
    # Ứng dụng của dự án — thứ tự migrate: users → sensors → devices (04-Database.md §8)
    "apps.core",
    "apps.users",
    "apps.sensors",
    "apps.devices",
    "apps.realtime",
    "apps.mqtt",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",   # đứng trước CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ⚠️ BẮT BUỘC có TRƯỚC lần `migrate` đầu tiên (04-Database.md §2.5).
# Khai sau khi đã migrate thì cách sửa duy nhất là DROP DATABASE rồi làm lại.
AUTH_USER_MODEL = "users.User"


# ---------------------------------------------------------------------------
# CSDL và Redis
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        # Bắt buộc PostgreSQL: /api/sensors/latest dùng DISTINCT ON (05-API.md §4.1)
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="iot_room"),
        "USER": env("DB_USER", default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"   # bigserial — 04-Database.md §4

# Redis là cầu nối giữa hai tiến trình daphne và mqtt_worker. Dùng InMemoryChannelLayer
# thì worker gọi group_send "thành công" mà không trình duyệt nào nhận được (05-API.md §5.5).
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [{
            "address": env("REDIS_URL", default="redis://localhost:6379/5"),
            # ⚠️ BẮT BUỘC > 5. redis-py 8 mặc định chờ đọc 5 giây, trùng đúng thời gian
            # channels_redis chờ tin mới (brpop_timeout = 5). Khi không có sự kiện nào trong
            # 5 giây (mạch ngoại tuyến) thì lệnh đọc báo TimeoutError trước, WebSocket sập,
            # trình duyệt nối lại sau 5 giây rồi lại sập — vòng lặp ~11 giây (đo 18/09/2026).
            "socket_timeout": 15,
        }]},
    }
}


# ---------------------------------------------------------------------------
# Ngôn ngữ và thời gian
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "vi"     # thông báo lỗi có sẵn của Django/DRF ra tiếng Việt
USE_I18N = True

# 05-API.md §2.4 — BẮT BUỘC "UTC": API luôn trả mốc thời gian có hậu tố Z.
# Đổi sang giờ Việt Nam để hiển thị là việc của Frontend.
TIME_ZONE = "UTC"
USE_TZ = True


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # 05-API.md §2.2 — CHỈ TokenAuthentication. Có SessionAuthentication đứng đầu thì
    # request thiếu token nhận 403 thay vì 401, Frontend không về được trang đăng nhập.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",       # BR-13
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "PAGE_SIZE": 10,                                        # BR-08
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "apps.core.filters.TiebreakOrderingFilter",          # 05-API.md §7.3 điểm 3
    ],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "IoT Room Monitoring API",
    "DESCRIPTION": (
        "Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT.\n\n"
        "Bấm **Authorize** và nhập `Token <token>` — có chữ `Token` và một dấu cách "
        "(lấy token bằng `POST /api/auth/login`)."
    ),
    "VERSION": "2.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Swagger mở được khi chưa đăng nhập (05-API.md §3.3) — đừng đổi
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
    # Device.State và ActionHistory.Action cùng là ON/OFF — đặt một tên chung cho Swagger
    "ENUM_NAME_OVERRIDES": {"OnOffEnum": "apps.devices.models.Device.State"},
}

# Frontend (Vite :5173) khác origin với backend (:8000) — 05-API.md §2.9.
# Không bật CORS_ALLOW_CREDENTIALS: token đi trong header, không đi bằng cookie.
CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)


# ---------------------------------------------------------------------------
# MQTT và quy tắc nghiệp vụ điều khiển
# ---------------------------------------------------------------------------

MQTT_HOST = env("MQTT_HOST", default="127.0.0.1")   # không dùng "localhost" — xem .env.example
MQTT_PORT = env("MQTT_PORT", default=1884, cast=int)
MQTT_USERNAME = env("MQTT_USERNAME", default="")
MQTT_PASSWORD = env("MQTT_PASSWORD", default="")
MQTT_CONNECT_TIMEOUT = env("MQTT_CONNECT_TIMEOUT", default=2.0, cast=float)

DEVICE_RESPONSE_TIMEOUT_SECONDS = 5     # BR-03
TIMEOUT_SWEEP_INTERVAL_SECONDS = 1      # SD-05 — nên timeout thực tế là 5–6 giây


# ---------------------------------------------------------------------------
# Trang Profile — dữ liệu tĩnh đọc từ .env, không có bảng CSDL (05-API.md §4.7)
# ---------------------------------------------------------------------------

def _env_or_none(name, default=""):
    """Biến để trống thì trả None — API trả `null`, không trả chuỗi rỗng."""
    return env(name, default=default) or None


PROFILE = {
    "student": {
        "full_name": _env_or_none("PROFILE_FULL_NAME"),
        "student_id": _env_or_none("PROFILE_STUDENT_ID"),
        "class_name": _env_or_none("PROFILE_CLASS"),
        "email": _env_or_none("PROFILE_EMAIL"),
        "avatar_url": _env_or_none("PROFILE_AVATAR_URL"),
    },
    "project": {
        "title": _env_or_none("PROJECT_TITLE"),
        "subject": _env_or_none("PROJECT_SUBJECT"),
        "supervisor": _env_or_none("PROJECT_SUPERVISOR"),
    },
    "links": {
        "github": _env_or_none("LINK_GITHUB"),
        "report_pdf": _env_or_none("LINK_REPORT_PDF"),
        "figma": _env_or_none("LINK_FIGMA"),
        "api_docs": _env_or_none("LINK_API_DOCS"),
    },
}


# ---------------------------------------------------------------------------
# Còn lại
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "config": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
