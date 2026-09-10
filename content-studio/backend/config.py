from pydantic_settings import BaseSettings
from typing import Optional
import warnings

class Settings(BaseSettings):
    # API Keys
    tikhub_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    siliconflow_api_key: str = ""
    deepgram_api_key: str = ""

    # AI Model Config
    use_deepseek: bool = True
    deepseek_base_url: str = "https://api.deepseek.com/anthropic"
    deepseek_model: str = "deepseek-chat"

    # TikHub 上游请求：偶发 TLS EOF 时有限重试，均可通过 .env 调整
    tikhub_connect_timeout_seconds: float = 15.0
    tikhub_read_timeout_seconds: float = 60.0
    tikhub_write_timeout_seconds: float = 30.0
    tikhub_pool_timeout_seconds: float = 15.0
    tikhub_max_retries: int = 2
    tikhub_retry_backoff_seconds: float = 0.8

    # DB
    database_url: str = "sqlite:///./content_studio.db"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # WeChat Official Account (公众号)
    wechat_appid: str = ""
    wechat_appsecret: str = ""
    wechat_token: str = "content_studio"  # 公众号服务器验证 Token

    # 支付配置。旧 YunGouOS 字段保留读取兼容，不再作为生产适配器。
    yungouos_wxpay_mchid: str = ""         # 微信支付商户号
    yungouos_alipay_mchid: str = ""        # 支付宝商户号
    yungouos_merge_mchid: str = ""         # 聚合支付商户号（一码付）
    yungouos_key: str = ""                 # 商户密钥
    yungouos_notify_url: str = ""          # 支付回调地址（需公网可访问）
    yungouos_base_url: str = "https://api.pay.yungouos.com/api/pay"
    payment_http_timeout_seconds: float = 15.0
    payment_order_expire_minutes: int = 15
    # 本地回调未及时到达时，订单查询接口可向 GGGUA 做兜底核验。
    payment_query_fallback: bool = True
    payment_query_interval_seconds: float = 10.0
    # 必须同时满足 DEBUG=true 和 PAYMENT_DEV_MODE=true 才允许模拟支付。
    # 这样即使部署时误把 DEBUG 打开，也不会意外开放免เงินจริง支付。
    payment_dev_mode: bool = False

    # GGGUA 易支付（https://pay.gggua.com/doc.html）
    payment_provider: str = "gggua"
    gggua_pid: str = ""
    gggua_key: str = ""
    # GGGUA_BASE_URL 是文档中的公共根地址；gggua_api_base 兼容早期本地配置。
    gggua_base_url: str = "https://pay.gggua.com"
    gggua_api_base: str = "https://pay.gggua.com"
    gggua_notify_url: str = ""
    gggua_return_url: str = ""
    # 支付请求中的 clientip。为空时由受信任的反向代理/请求地址推导。
    gggua_client_ip: str = ""
    # 逗号分隔的受信任代理地址；不要把任意 X-Forwarded-For 当作用户 IP。
    payment_trusted_proxy_ips: str = "127.0.0.1,::1"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    # 部署环境访问不到 Google（如境内服务器）时置 false，登录页据此隐藏入口。
    google_oauth_enabled: bool = True

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""

    # JWT
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24 * 7         # 7天
    allow_insecure_jwt_secret: bool = False

    # Admin init protection（首次初始化管理员所需密钥，留空则禁用 /admin/init 接口）
    admin_init_token: str = ""

    # Email verification
    email_verify_enabled: bool = True
    email_verify_expire_hours: int = 24
    backend_public_url: str = "http://localhost:8080"
    email_otp_debug_echo: bool = False

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    email_from: str = ""
    email_from_name: str = "文策引擎"

    # Subscription pricing
    monthly_price_fen: int = 4900          # ¥49.00 in fen
    trial_days: int = 1

    # App
    app_name: str = "文策引擎"
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
        "https://wence.tongzhuo.ink",
    ]
    frontend_url: str = "http://localhost:5173"

    # Public OpenAPI for content generation
    open_api_enabled: bool = False
    open_api_key: str = ""
    open_api_user_id: int = 0
    open_api_require_subscription: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

def _is_weak_jwt_secret(secret: str) -> bool:
    raw = (secret or "").strip()
    weak_values = {
        "",
        "change-me-in-production-use-long-random-string",
        "secret",
        "123456",
        "password",
    }
    return len(raw) < 32 or raw in weak_values


if _is_weak_jwt_secret(settings.jwt_secret):
    msg = (
        "\n⚠️  JWT_SECRET 强度不足（不能为空且至少 32 字符）。\n"
        "   请在 .env 中设置强随机字符串。\n"
        "   例如: JWT_SECRET=请替换为至少32位随机值\n"
    )
    if settings.debug or settings.allow_insecure_jwt_secret:
        warnings.warn(msg + "   当前为开发放行模式，仅用于本地调试。\n", stacklevel=1)
    else:
        raise RuntimeError(msg)
