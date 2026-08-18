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

    # DB
    database_url: str = "sqlite:///./content_studio.db"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # WeChat Official Account (公众号)
    wechat_appid: str = ""
    wechat_appsecret: str = ""
    wechat_token: str = "content_studio"  # 公众号服务器验证 Token

    # YunGouOS 支付
    yungouos_wxpay_mchid: str = ""         # 微信支付商户号
    yungouos_alipay_mchid: str = ""        # 支付宝商户号
    yungouos_merge_mchid: str = ""         # 聚合支付商户号（一码付）
    yungouos_key: str = ""                 # 商户密钥
    yungouos_notify_url: str = ""          # 支付回调地址（需公网可访问）

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""

    # JWT
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24 * 7         # 7天
    allow_insecure_jwt_secret: bool = False

    # Subscription pricing
    monthly_price_fen: int = 4900          # ¥49.00 in fen
    trial_days: int = 1

    # App
    app_name: str = "文策引擎"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"]
    frontend_url: str = "http://localhost:5173"

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
