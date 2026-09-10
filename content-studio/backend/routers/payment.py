"""支付路由：GGGUA 易支付下单、异步通知和订阅权益发放。

供应商协议细节集中在本模块的 GGGUA helper 中，路由层只保存本地订单并把
供应商状态归一化成现有客户端使用的 pending/paid/closed/refunded 状态。
真实商户参数只从 settings 读取，绝不写入仓库或返回给客户端。
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import os
import re
import threading
import time
import uuid
import base64
from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal, DecimalException
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import PaymentOrder, Subscription, User
from .deps import get_current_user


logger = logging.getLogger("content_studio.payment")
router = APIRouter(prefix="/payment", tags=["payment"])

# Provider lookups are throttled per process so a browser polling every few
# seconds does not turn into an equal-rate upstream API flood.  The callback
# remains the primary settlement path; this cache only controls the optional
# read-only reconciliation fallback.
_provider_query_last_at: dict[int, float] = {}
# SQLite does not implement row-level ``SELECT .. FOR UPDATE`` locking, and
# development mode is intentionally useful with the local SQLite database.
# Serialize the in-process simulated settlement path so two rapid clicks cannot
# extend one subscription twice.  Production callbacks still use the database
# row lock below (and this lock also protects a single-worker SQLite process).
_dev_payment_lock = threading.Lock()

GGGUA_DEFAULT_BASE = "https://pay.gggua.com"
GGGUA_METHODS = {"wechat": "wxpay", "alipay": "alipay"}
# Provider checkout entry points are persisted and, for ``qrcode``, rendered
# into a bitmap.  Bound their size before either operation so a malformed or
# compromised upstream response cannot trigger unbounded storage/QR work.
GGGUA_ENTRY_MAX_LENGTH = 4096
GGGUA_MONEY_MAX_LENGTH = 20
_PAYMENT_METHOD_ALIASES = {
    "wechat": "wechat",
    "wxpay": "wechat",
    "wx": "wechat",
    "alipay": "alipay",
    "ali": "alipay",
}
GGGUA_PAYMENT_METHODS = tuple(GGGUA_METHODS.keys())


class PaymentConfigurationError(RuntimeError):
    """GGGUA 商户配置不完整或不安全。"""


class PaymentProviderError(RuntimeError):
    """GGGUA 上游请求失败或响应格式不正确。"""


class CreateOrderRequest(BaseModel):
    method: str = "wechat"
    plan: str = "monthly"


def _setting(name: str, default: Any = "") -> Any:
    """兼容旧 Settings 类，避免尚未升级的运行环境导入失败。"""
    return getattr(settings, name, default)


def _normalise_method(method: Any) -> str:
    raw = str(method or "").strip().lower()
    return _PAYMENT_METHOD_ALIASES.get(raw, raw)


def _gggua_base_url() -> str:
    # ``GGGUA_BASE_URL`` is the documented setting.  ``GGGUA_API_BASE`` was
    # used by the first local draft, so retain it only as a fallback.  When a
    # test/old deployment overrides the legacy value while the new setting is
    # still its default, prefer the override.
    configured = str(_setting("gggua_base_url", "") or "").strip()
    legacy = str(_setting("gggua_api_base", "") or "").strip()
    if not configured or (configured == GGGUA_DEFAULT_BASE and legacy and legacy != GGGUA_DEFAULT_BASE):
        configured = legacy
    value = (configured or GGGUA_DEFAULT_BASE).rstrip("/")
    if not value:
        value = GGGUA_DEFAULT_BASE
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    local_hosts = {"localhost", "127.0.0.1", "::1", "testserver"}
    allowed_hosts = {
        "pay.gggua.com",
        "www.pay.gggua.com",
        "api.pay.gggua.com",
    }
    if parsed.scheme not in {"http", "https"} or not host:
        raise PaymentConfigurationError("GGGUA_BASE_URL 必须是完整的 HTTP(S) 地址")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise PaymentConfigurationError("GGGUA_BASE_URL 不得包含账号、查询参数或片段")
    if host not in allowed_hosts:
        # Local HTTP endpoints are useful for an isolated test server, but
        # cannot accidentally be enabled in production.
        if not (_setting("debug", False) and host in local_hosts):
            raise PaymentConfigurationError("GGGUA_BASE_URL 主机必须是 pay.gggua.com")
    if parsed.scheme != "https" and not (_setting("debug", False) and host in local_hosts):
        raise PaymentConfigurationError("生产 GGGUA_BASE_URL 必须使用 HTTPS")
    try:
        port = parsed.port
    except ValueError as exc:
        raise PaymentConfigurationError("GGGUA_BASE_URL 端口无效") from exc
    if host in allowed_hosts and port not in (None, 443):
        raise PaymentConfigurationError("生产 GGGUA_BASE_URL 只能使用 HTTPS 默认端口")
    return value


def _gggua_config_errors(
    *, require_notify: bool = True, validate_optional_urls: bool = True
) -> list[str]:
    missing: list[str] = []
    provider = str(_setting("payment_provider", "gggua") or "gggua").strip().lower()
    if provider != "gggua":
        missing.append("PAYMENT_PROVIDER=gggua")
    if not str(_setting("gggua_pid", "") or "").strip():
        missing.append("GGGUA_PID")
    if not str(_setting("gggua_key", "") or "").strip():
        missing.append("GGGUA_KEY")
    # ``return_url`` is optional in GGGUA V1.  Validate it only when explicitly
    # configured; a local development ``FRONTEND_URL`` must not accidentally
    # make production payments unavailable or be sent as an HTTP redirect.
    if require_notify:
        raw_notify = str(_setting("gggua_notify_url", "") or "").strip()
        if not raw_notify:
            missing.append("GGGUA_NOTIFY_URL")
        else:
            try:
                _validate_public_url(
                    raw_notify,
                    "GGGUA_NOTIFY_URL",
                    allow_local=bool(_setting("debug", False)),
                )
            except PaymentConfigurationError:
                missing.append("GGGUA_NOTIFY_URL")
    if validate_optional_urls:
        raw_return = str(_setting("gggua_return_url", "") or "").strip()
        if raw_return:
            try:
                _validate_public_url(
                    raw_return,
                    "GGGUA_RETURN_URL",
                    allow_local=bool(_setting("debug", False)),
                )
            except PaymentConfigurationError:
                missing.append("GGGUA_RETURN_URL")
    try:
        _gggua_base_url()
    except PaymentConfigurationError:
        missing.append("GGGUA_API_BASE")
    return missing


def _gggua_is_configured() -> bool:
    return not _gggua_config_errors()


def _gggua_notify_url() -> str:
    return str(_setting("gggua_notify_url", "") or "").strip()


def _gggua_return_url() -> str:
    return str(_setting("gggua_return_url", "") or "").strip()


def _validate_public_url(value: str, label: str, *, allow_local: bool = False) -> str:
    """Validate callback/return URLs before sending them to the provider."""
    parsed = urlparse(str(value or "").strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    local_hosts = {"localhost", "127.0.0.1", "::1", "testserver"}
    if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
        raise PaymentConfigurationError(f"{label} 必须是完整的 HTTP(S) 地址")
    if parsed.query or parsed.fragment:
        raise PaymentConfigurationError(f"{label} 不得包含查询参数或片段")
    if parsed.scheme != "https" and not (allow_local and host in local_hosts):
        raise PaymentConfigurationError(f"{label} 生产环境必须使用 HTTPS")
    if host in local_hosts and not allow_local:
        raise PaymentConfigurationError(f"{label} 不能使用本机地址")
    return str(value).strip()


def _payment_dev_enabled() -> bool:
    """模拟支付必须同时由 DEBUG 和 PAYMENT_DEV_MODE 显式打开。"""
    disabled = str(os.environ.get("DISABLE_DEV_PAY", "")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return bool(
        _setting("debug", False)
        and _setting("payment_dev_mode", False)
        and not disabled
    )


def _gggua_sign(params: Mapping[str, Any], key: Optional[str] = None) -> str:
    """生成 GGGUA 易支付 MD5 签名。

    过滤 sign、sign_type 和空值，按 ASCII key 排序，不做 URL 编码，最后将
    商户密钥直接拼接到 canonical 字符串（GGGUA V1 规则）后计算 MD5 小写。
    """
    secret = str(_setting("gggua_key", "") if key is None else (key or "")).strip()
    filtered: dict[str, str] = {}
    for raw_name, raw_value in params.items():
        name = str(raw_name)
        if name.lower() in {"sign", "sign_type"} or raw_value in (None, ""):
            continue
        filtered[name] = str(raw_value)
    canonical = "&".join(
        f"{name}={filtered[name]}" for name in sorted(filtered.keys())
    )
    return hashlib.md5((canonical + secret).encode("utf-8")).hexdigest().lower()


def _verify_gggua_sign(params: Mapping[str, Any]) -> bool:
    """严格验证回调签名；未配置密钥时永远失败。"""
    supplied = str(params.get("sign", "") or "").strip().lower()
    secret = str(_setting("gggua_key", "") or "").strip()
    if not supplied or not secret:
        return False
    # sign_type is mandatory on a callback; accepting an omitted value would
    # make a malformed/legacy payload indistinguishable from an MD5 callback.
    if "sign_type" not in params:
        return False
    sign_type = str(params.get("sign_type", "") or "").strip().upper()
    if sign_type != "MD5":
        return False
    expected = _gggua_sign(params, secret)
    return hmac.compare_digest(supplied, expected)


# Backward-compatible names used by the pre-GGGUA unit test module.  Runtime
# notification handling never calls these helpers; they retain the historical
# YunGouOS test vector so an old local test suite does not break merely because
# the production provider changed.
def _yungouos_sign(params: Mapping[str, Any]) -> str:
    filtered = {
        str(name): str(value)
        for name, value in params.items()
        if value not in (None, "") and str(name) != "sign"
    }
    canonical = "&".join(f"{name}={filtered[name]}" for name in sorted(filtered))
    raw = f"{canonical}&key={str(_setting('yungouos_key', '') or '')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def _verify_notify_sign(params: Mapping[str, Any]) -> bool:
    supplied = str(params.get("sign", "") or "")
    if not supplied:
        return False
    return hmac.compare_digest(supplied.upper(), _yungouos_sign(params).upper())


def _money_to_fen(value: Any) -> Optional[int]:
    """精确地把元转换为分，拒绝非法、负数和超过两位小数。"""
    if value is None:
        return None
    raw = str(value).strip()
    if len(raw) > GGGUA_MONEY_MAX_LENGTH:
        return None
    # Decimal accepts exponent notation (``1e2``), signs and arbitrary
    # precision.  Payment callbacks must use the provider's plain Yuan format
    # and never be rounded implicitly.
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", raw):
        return None
    try:
        amount = Decimal(raw)
    except (DecimalException, TypeError, ValueError, OverflowError):
        return None
    if not amount.is_finite() or amount < 0:
        return None
    if amount.as_tuple().exponent < -2:
        return None
    try:
        fen = amount * Decimal(100)
        if fen != fen.to_integral_value():
            return None
        return int(fen)
    except (DecimalException, TypeError, ValueError, OverflowError):
        return None


def _amount_yuan(amount_fen: int) -> str:
    return f"{Decimal(int(amount_fen)) / Decimal(100):.2f}"


def _monthly_price_fen() -> int:
    """Return a safe positive configured monthly price, or zero if invalid."""
    try:
        value = int(_setting("monthly_price_fen", 0) or 0)
    except (TypeError, ValueError, OverflowError):
        logger.error("monthly_price_fen is not a valid integer")
        return 0
    return value if value > 0 else 0


def _qr_data_uri(payload: Any) -> Optional[str]:
    """Render a provider payment URI as a local PNG data URI.

    GGGUA's ``qrcode`` field is a URI such as ``weixin://...``; browsers must
    not receive that value as ``<img src>``.  The optional dependency is part
    of both runtime requirement files.  A missing dependency leaves the raw
    payload available to the frontend instead of leaking a non-image scheme.
    """
    text = str(payload or "").strip()
    if not text:
        return None
    if len(text) > GGGUA_ENTRY_MAX_LENGTH:
        raise PaymentProviderError("GGGUA 支付入口内容过长")
    try:
        import qrcode
    except ImportError:
        logger.error("qrcode[pil] is not installed; returning payment payload only")
        return None
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        output = BytesIO()
        image.save(output, format="PNG")
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception as exc:  # pragma: no cover - provider data/library errors
        logger.exception("failed to render GGGUA QR payload")
        raise PaymentProviderError("支付二维码生成失败") from exc


def _timeout_seconds() -> float:
    try:
        return max(1.0, float(_setting("payment_http_timeout_seconds", 15.0)))
    except (TypeError, ValueError):
        return 15.0


def _order_expire_at() -> Optional[datetime]:
    if not hasattr(PaymentOrder, "expires_at"):
        return None
    try:
        minutes = max(1, int(_setting("payment_order_expire_minutes", 15)))
    except (TypeError, ValueError):
        minutes = 15
    return datetime.utcnow() + timedelta(minutes=minutes)


def _is_expired(order: PaymentOrder) -> bool:
    expires_at = getattr(order, "expires_at", None)
    return bool(expires_at and expires_at <= datetime.utcnow())


def _build_gggua_params(
    order_no: str,
    amount_yuan: str,
    method: str,
    *,
    client_ip: str = "",
    device: str = "pc",
    param: str = "",
) -> dict[str, str]:
    """构造 mapi.php 完整表单；所有字段加入后才计算 sign。"""
    normalised = _normalise_method(method)
    if normalised not in GGGUA_METHODS:
        raise PaymentConfigurationError("GGGUA 仅支持微信和支付宝")
    if not _gggua_is_configured():
        missing = ", ".join(_gggua_config_errors())
        raise PaymentConfigurationError(f"支付参数未配置: {missing}")
    fields: dict[str, str] = {
        "pid": str(_setting("gggua_pid", "")).strip(),
        "type": GGGUA_METHODS[normalised],
        "out_trade_no": str(order_no),
        "notify_url": _gggua_notify_url(),
        "name": "文策引擎 标准版 - 1个月",
        "money": str(amount_yuan),
        "device": str(device or "pc"),
        "param": str(param or ""),
        "sign_type": "MD5",
    }
    return_url = _gggua_return_url()
    if return_url:
        fields["return_url"] = return_url
    normalized_ip = str(client_ip or "").strip()
    if not normalized_ip:
        raise PaymentConfigurationError("GGGUA clientip 不能为空")
    try:
        normalized_ip = str(ipaddress.ip_address(normalized_ip))
    except ValueError as exc:
        raise PaymentConfigurationError("GGGUA clientip 格式无效") from exc
    fields["clientip"] = normalized_ip
    fields["sign"] = _gggua_sign(fields)
    return fields


def _request_client_ip(request: Request) -> str:
    """Return a validated client IP without trusting arbitrary forwarded headers.

    A configured ``GGGUA_CLIENT_IP`` wins when it is a literal IP.  Otherwise
    ``X-Forwarded-For`` is considered only when the immediate peer is listed
    in ``PAYMENT_TRUSTED_PROXY_IPS``; direct callers use the socket peer.
    """
    configured = str(_setting("gggua_client_ip", "") or "").strip()
    try:
        if configured:
            return str(ipaddress.ip_address(configured))
    except ValueError:
        logger.warning("Ignoring invalid GGGUA_CLIENT_IP")

    peer = str(request.client.host if request.client else "").strip()
    trusted_raw = str(_setting("payment_trusted_proxy_ips", "") or "")
    trusted: set[str] = set()
    for item in trusted_raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            trusted.add(str(ipaddress.ip_address(item)))
        except ValueError:
            continue

    if peer in trusted:
        # Walk from the immediate proxy toward the client (right to left).
        # Skip configured proxy hops and use the first valid non-proxy address;
        # this prevents an untrusted left-most header value from overriding a
        # real client address appended by the proxy.
        for candidate in reversed(request.headers.get("x-forwarded-for", "").split(",")):
            candidate = candidate.strip()
            try:
                parsed_candidate = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            normalized_candidate = str(parsed_candidate)
            if normalized_candidate not in trusted:
                return normalized_candidate
    try:
        client_ip = str(ipaddress.ip_address(peer))
    except ValueError:
        client_ip = ""
    if not client_ip and bool(_setting("debug", False)) and peer in {
        "testclient", "testserver", "localhost"
    }:
        client_ip = "127.0.0.1"
    if not client_ip:
        raise PaymentConfigurationError("无法确定支付请求 clientip")
    return client_ip


def _first_value(source: Mapping[str, Any], *names: str) -> Optional[str]:
    lower_map = {str(key).lower(): value for key, value in source.items()}
    for name in names:
        value = source.get(name)
        if value in (None, ""):
            value = lower_map.get(name.lower())
        if value not in (None, ""):
            text = str(value).strip()
            if text:
                return text
    return None


def _consistent_value(source: Mapping[str, Any], *names: str) -> Optional[str]:
    """Read aliases while rejecting a payload that contains conflicting values."""
    aliases = {str(name).lower() for name in names}
    values: list[str] = []
    for key, raw_value in source.items():
        if str(key).lower() not in aliases or raw_value in (None, ""):
            continue
        value = str(raw_value).strip()
        if value:
            values.append(value)
    unique = list(dict.fromkeys(values))
    if len(unique) != 1:
        return None
    return unique[0]


def _single_value(source: Mapping[str, Any], *names: str) -> Optional[str]:
    """Read one callback field and reject repeated aliases outright.

    ``trade_no`` and ``tradeNo`` are compatibility aliases, but accepting both
    in one signed payload makes it impossible to tell whether a proxy merged
    two parameter sources.  Callback business fields therefore require exactly
    one non-empty occurrence.
    """
    aliases = {str(name).lower() for name in names}
    values: list[str] = []
    occurrences = 0
    for key, raw_value in source.items():
        if str(key).lower() not in aliases or raw_value is None:
            continue
        occurrences += 1
        value = str(raw_value).strip()
        values.append(value)
    if occurrences != 1 or not values[0]:
        return None
    return values[0]


def _response_data(payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get("data")
    if isinstance(nested, Mapping):
        # Prefer non-empty top-level values while retaining nested fields.  A
        # number of gateways return ``data`` plus an empty top-level alias.
        merged = dict(nested)
        for key, value in payload.items():
            if key == "data" or value in (None, ""):
                continue
            merged[key] = value
        return merged
    if isinstance(nested, str) and nested.strip():
        merged = dict(payload)
        merged.setdefault("qrcode", nested.strip())
        return merged
    return dict(payload)


def _parse_gggua_create_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise PaymentProviderError("GGGUA 返回格式无效")
    if str(payload.get("code", "")) != "1":
        raise PaymentProviderError("GGGUA 下单失败")
    data = _response_data(payload)
    def _one_alias(*names: str) -> Optional[str]:
        values: list[str] = []
        for name in names:
            value = _first_value(data, name)
            if value and len(value) > GGGUA_ENTRY_MAX_LENGTH:
                raise PaymentProviderError("GGGUA 支付入口内容过长")
            if value and value not in values:
                values.append(value)
        if len(values) > 1:
            raise PaymentProviderError("GGGUA 返回了冲突的支付入口")
        return values[0] if values else None

    trade_no = _consistent_value(data, "trade_no", "tradeNo")
    if not trade_no or len(trade_no) > 100:
        raise PaymentProviderError("GGGUA 未返回有效的第三方流水号")

    payurl = _one_alias("payurl", "pay_url", "payUrl")
    qrcode = _one_alias("qrcode", "qr_code", "qrCode")
    urlscheme = _one_alias("urlscheme", "url_scheme", "urlScheme")
    entries = [("payurl", payurl), ("qrcode", qrcode), ("urlscheme", urlscheme)]
    present = [(name, value) for name, value in entries if value]
    if len(present) != 1:
        raise PaymentProviderError(
            "GGGUA 必须且只能返回 payurl、qrcode、urlscheme 其中一项"
        )
    entry_name, payment_url = present[0]
    # qrcode is a payment URI, not a bitmap image.  Materialise a local PNG
    # only for the qrcode form.  ``payurl`` is a browser payment page and
    # ``urlscheme`` is an app deep link; turning either into a QR image would
    # hide the protocol's intended action from the client.
    qr_payload = str(payment_url)
    qr_code_url = _qr_data_uri(qr_payload) if entry_name == "qrcode" else None
    return {
        "trade_no": trade_no,
        "payurl": payurl,
        "qrcode": qrcode,
        "urlscheme": urlscheme,
        "pay_url": payurl,
        "qr_payload": qr_payload if entry_name == "qrcode" else None,
        "qr_code_url": qr_code_url,
        "qr_code_is_url": False,
        "entry_type": entry_name,
    }


async def _post_gggua_json(
    url: str, params: Mapping[str, Any]
) -> Mapping[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            response = await client.post(url, data=dict(params))
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise PaymentProviderError("支付服务暂时不可用") from exc
    if not isinstance(payload, Mapping):
        raise PaymentProviderError("支付服务返回格式无效")
    return payload


async def _create_gggua_payment(
    order_no: str,
    amount_yuan: str,
    method: str,
    *,
    client_ip: str = "",
    device: str = "pc",
    param: str = "",
) -> dict[str, Any]:
    params = _build_gggua_params(
        order_no,
        amount_yuan,
        method,
        client_ip=client_ip,
        device=device,
        param=param,
    )
    payload = await _post_gggua_json(f"{_gggua_base_url()}/mapi.php", params)
    return _parse_gggua_create_response(payload)


async def _create_wxpay_native(
    order_no: str, amount_yuan: str, body_text: str
) -> str:
    result = await _create_gggua_payment(
        order_no, amount_yuan, "wechat", param=body_text
    )
    return str(
        result.get("qr_code_url")
        or result.get("pay_url")
        or result.get("urlscheme")
        or ""
    )


async def _create_alipay_native(
    order_no: str, amount_yuan: str, body_text: str
) -> str:
    result = await _create_gggua_payment(
        order_no, amount_yuan, "alipay", param=body_text
    )
    return str(
        result.get("qr_code_url")
        or result.get("pay_url")
        or result.get("urlscheme")
        or ""
    )


async def _create_merge_native(
    order_no: str, amount_yuan: str, body_text: str
) -> str:
    raise PaymentConfigurationError("GGGUA 不支持 merge 支付方式")


async def _query_gggua_order(
    *,
    out_trade_no: Optional[str] = None,
    trade_no: Optional[str] = None,
) -> dict[str, Any]:
    """查询单笔订单：GET api.php?act=order。"""
    if not out_trade_no and not trade_no:
        raise ValueError("out_trade_no 或 trade_no 至少提供一个")
    query_config_errors = _gggua_config_errors(
        require_notify=False, validate_optional_urls=False
    )
    if query_config_errors:
        missing = ", ".join(query_config_errors)
        raise PaymentConfigurationError(f"支付参数未配置: {missing}")
    params: dict[str, str] = {
        "act": "order",
        "pid": str(_setting("gggua_pid", "")).strip(),
        "key": str(_setting("gggua_key", "")).strip(),
    }
    if out_trade_no:
        params["out_trade_no"] = str(out_trade_no)
    if trade_no:
        params["trade_no"] = str(trade_no)
    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            response = await client.get(f"{_gggua_base_url()}/api.php", params=params)
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise PaymentProviderError("支付服务暂时不可用") from exc
    if not isinstance(payload, Mapping):
        raise PaymentProviderError("GGGUA 查询订单失败")
    data = payload.get("data")
    if isinstance(data, Mapping):
        result = dict(data)
        # Preserve status/code aliases returned alongside a nested ``data``.
        for key in ("status", "trade_status", "tradeStatus", "code", "msg"):
            if key in payload and key not in result:
                result[key] = payload[key]
    else:
        result = dict(payload)
    # V1 query responses use ``code=1`` for a successful query and
    # ``data.status=1`` for a paid order.  Do not accept a contradictory or
    # missing code merely because a nested status happens to look successful.
    code = result.get("code", payload.get("code"))
    status = result.get("status", result.get("trade_status", result.get("tradeStatus")))
    if str(code) not in {"1", "True", "true"}:
        raise PaymentProviderError("GGGUA 查询订单失败")
    if status is None:
        raise PaymentProviderError("GGGUA 查询订单返回缺少状态")
    return result


query_gggua_order = _query_gggua_order


def _provider_query_due(order_id: int) -> bool:
    """Return whether the optional provider reconciliation lookup is due."""
    if not bool(_setting("payment_query_fallback", True)):
        return False
    try:
        interval = max(1.0, float(_setting("payment_query_interval_seconds", 10.0)))
    except (TypeError, ValueError):
        interval = 10.0
    now = time.monotonic()
    last = _provider_query_last_at.get(int(order_id), 0.0)
    if now - last < interval:
        return False
    _provider_query_last_at[int(order_id)] = now
    # Keep this process-local guard bounded in long-running workers.
    if len(_provider_query_last_at) > 10000:
        cutoff = now - max(interval * 10, 60.0)
        for key, timestamp in list(_provider_query_last_at.items()):
            if timestamp < cutoff:
                _provider_query_last_at.pop(key, None)
    return True


def _query_result_is_paid(result: Mapping[str, Any], order: PaymentOrder) -> Optional[str]:
    """Validate a paid query result and return its GGGUA trade number."""
    # The documented query response uses ``status=1`` while some compatible
    # gateways also include ``trade_status=TRADE_SUCCESS``.  Accept equivalent
    # aliases when they agree, but reject contradictory values instead of
    # letting whichever key happens to be read first decide settlement.
    status_values: list[str] = []
    status_aliases = {"status", "trade_status", "tradestatus"}
    for key, raw_value in result.items():
        if str(key).lower() not in status_aliases or raw_value in (None, ""):
            continue
        value = str(raw_value).strip().upper()
        if value in {"1", "TRUE", "PAID", "SUCCESS", "TRADE_SUCCESS"}:
            value = "PAID"
        elif value in {"0", "FALSE", "PENDING", "UNPAID", "TRADE_PENDING"}:
            value = "UNPAID"
        status_values.append(value)
    if not status_values or len(set(status_values)) != 1 or status_values[0] != "PAID":
        return None
    pid = _consistent_value(result, "pid")
    if pid is not None and pid != str(_setting("gggua_pid", "") or "").strip():
        return None
    out_trade_no = _consistent_value(result, "out_trade_no", "outTradeNo")
    if out_trade_no is not None and out_trade_no != order.order_no:
        return None
    callback_type = (_consistent_value(result, "type") or "").lower()
    expected_type = GGGUA_METHODS.get(_normalise_method(order.method))
    if not expected_type or callback_type != expected_type:
        return None
    money = _money_to_fen(_consistent_value(result, "money"))
    if money is None or money != int(order.amount_fen):
        return None
    trade_no = _consistent_value(result, "trade_no", "tradeNo")
    if not trade_no or len(trade_no) > 100:
        return None
    saved = str(order.transaction_id or "").strip()
    if saved and saved != trade_no:
        return None
    return trade_no


async def _reconcile_order_from_provider(
    db: Session, order: PaymentOrder, *, allow_expired: bool = False
) -> None:
    """Best-effort paid-state reconciliation when an async callback is late."""
    # Accessing an expired ORM instance can itself issue a SELECT, which would
    # trigger autoflush before the reconciliation checks below.  Keep all
    # reads of the caller-supplied order inside this guard; the only intended
    # flush boundary is the explicit commit after the conditional settlement.
    with db.no_autoflush:
        if (
            _payment_dev_enabled()
            or order.status != "pending"
            or (not allow_expired and _is_expired(order))
            or not _provider_query_due(order.id)
        ):
            return
        order_no = str(order.order_no)
    # Query only needs pid/key/base; notify_url may be temporarily absent while
    # an operator is diagnosing a deployment.  It never grants access without
    # matching the complete local order fields below.
    if _gggua_config_errors(require_notify=False, validate_optional_urls=False):
        return
    try:
        result = await _query_gggua_order(out_trade_no=order_no)
    except (PaymentConfigurationError, PaymentProviderError) as exc:
        logger.warning("GGGUA order reconciliation failed for %s: %s", order_no, exc)
        return
    with db.no_autoflush:
        trade_no = _query_result_is_paid(result, order)
    if not trade_no:
        return
    try:
        # A caller can hold a stale/dirty ORM instance (for example after
        # persisting the provider trade number while another callback is
        # reconciling the same order).  The locking query must not implicitly
        # flush that value before we have revalidated it against the durable
        # row; an autoflush IntegrityError here would escape as a 500 and stop
        # the normal retry path.  The explicit commit below remains the flush
        # boundary after all checks and the conditional state transition.
        with db.no_autoflush:
            locked = db.query(PaymentOrder).filter(
                PaymentOrder.id == order.id
            ).with_for_update().first()
            if (
                not locked
                or locked.status != "pending"
                or (not allow_expired and _is_expired(locked))
            ):
                return
            saved = str(locked.transaction_id or "").strip()
            if saved and saved != trade_no:
                return
            if not _mark_order_paid(
                db, locked, trade_no, allow_expired=allow_expired
            ):
                db.rollback()
                return
            db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("GGGUA reconciliation hit a duplicate transaction for %s", order_no)


def _activate_subscription(db: Session, user_id: int, plan: str) -> None:
    now = datetime.utcnow()
    duration = timedelta(days=30)
    # Lock the owning user before reading/updating the one-to-one subscription.
    # This serializes concurrent successful orders for one account on MySQL and
    # prevents two callbacks from both extending from the same old expiry.
    db.query(User.id).filter(User.id == user_id).with_for_update().first()
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub:
        current_expire = sub.expire_at or now
        base = current_expire if current_expire > now else now
        sub.plan = plan
        sub.expire_at = base + duration
        sub.is_active = True
        sub.updated_at = now
    else:
        db.add(
            Subscription(
                user_id=user_id,
                plan=plan,
                started_at=now,
                expire_at=now + duration,
                is_active=True,
            )
        )


def _mark_order_paid(
    db: Session,
    order: PaymentOrder,
    transaction_id: Optional[str],
    *,
    allow_expired: bool = False,
) -> bool:
    # ``with_for_update`` is ignored by SQLite and can also be bypassed by a
    # second process.  Make the state transition itself conditional so only
    # one callback/reconciliation worker can win the pending -> paid race.
    if order.status != "pending":
        return False
    now = datetime.utcnow()
    conditions = [
        PaymentOrder.id == order.id,
        PaymentOrder.status == "pending",
    ]
    if not allow_expired:
        conditions.append(
            or_(
                PaymentOrder.expires_at.is_(None),
                PaymentOrder.expires_at > now,
            )
        )
    result = db.execute(
        update(PaymentOrder)
        .where(*conditions)
        .values(
            status="paid",
            transaction_id=transaction_id or None,
            paid_at=now,
        )
    )
    if int(result.rowcount or 0) != 1:
        return False
    # Keep the caller's ORM instance coherent for response/duplicate checks;
    # the database predicate above, rather than this in-memory assignment, is
    # the authoritative concurrency gate.
    order.status = "paid"
    order.transaction_id = transaction_id or None
    order.paid_at = now
    _activate_subscription(db, order.user_id, order.plan)
    return True


def _order_to_dict(order: PaymentOrder) -> dict[str, Any]:
    expires_at = getattr(order, "expires_at", None)
    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "amount_fen": order.amount_fen,
        "method": order.method,
        "plan": order.plan,
        "qr_code_url": order.qr_code_url,
        "pay_url": getattr(order, "pay_url", None),
        "qr_payload": getattr(order, "qr_payload", None),
        "urlscheme": getattr(order, "url_scheme", None),
        "status": order.status,
        "transaction_id": order.transaction_id,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }


def _order_has_payment_entry(order: PaymentOrder) -> bool:
    """Whether a reserved order already has enough data for the client."""
    return bool(
        getattr(order, "pay_url", None)
        or getattr(order, "qr_code_url", None)
        or getattr(order, "qr_payload", None)
        or getattr(order, "url_scheme", None)
    )


def _mock_payment_result(order_no: str) -> dict[str, Any]:
    value = f"devpay://{order_no}"
    return {
        "pay_url": value,
        "qr_code_url": _qr_data_uri(value),
        "qr_payload": value,
        "qrcode": value,
        "urlscheme": value,
        "qr_code_is_url": False,
    }


@router.get("/config")
def payment_config() -> dict[str, Any]:
    """公开支付能力摘要，不泄露 pid、密钥或回调地址。"""
    amount_fen = _monthly_price_fen()
    amount = {
        "amount_fen": amount_fen if amount_fen > 0 else None,
        "amount_yuan": _amount_yuan(amount_fen) if amount_fen > 0 else None,
    }
    if _payment_dev_enabled():
        return {
            "available": True,
            "methods": list(GGGUA_PAYMENT_METHODS),
            "mode": "development",
            **amount,
        }
    configured = _gggua_is_configured()
    return {
        "available": configured,
        "methods": list(GGGUA_PAYMENT_METHODS) if configured else [],
        "mode": "gggua" if configured else "unavailable",
        **amount,
    }


@router.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    method = _normalise_method(body.method)
    if body.plan != "monthly":
        raise HTTPException(status_code=400, detail="暂只支持月度套餐")
    if method not in GGGUA_METHODS:
        raise HTTPException(status_code=400, detail="method 须为 wechat 或 alipay")

    amount_fen = _monthly_price_fen()
    if amount_fen <= 0:
        raise HTTPException(status_code=503, detail="支付金额未正确配置")
    dev_mode = _payment_dev_enabled()
    if not dev_mode and not _gggua_is_configured():
        raise HTTPException(
            status_code=503,
            detail="支付暂不可用，请联系管理员配置 GGGUA 商户参数",
        )
    key = (idempotency_key or "").strip()
    if len(key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key 长度不能超过 128")
    existing = None
    if key and hasattr(PaymentOrder, "idempotency_key"):
        existing = db.query(PaymentOrder).filter(
            PaymentOrder.user_id == current_user.id,
            PaymentOrder.idempotency_key == key,
        ).first()
        if existing:
            if _normalise_method(existing.method) != method or existing.plan != body.plan:
                raise HTTPException(status_code=409, detail="幂等键已用于其他订单")
            if existing.status != "pending":
                return _order_to_dict(existing)
            # A local reservation must never be used to create a fresh
            # provider order after its checkout window has elapsed.  Keep the
            # row pending so a late, valid provider callback can still settle
            # it; the client receives a clear conflict and rotates its key for
            # a genuinely new checkout attempt.
            if _is_expired(existing):
                # The client may be retrying after losing the original mapi
                # response.  Reconcile once before returning the expiry error
                # so a paid provider order can still activate the subscription.
                await _reconcile_order_from_provider(
                    db, existing, allow_expired=True
                )
                db.refresh(existing)
                if existing.status != "pending":
                    return _order_to_dict(existing)
                raise HTTPException(status_code=409, detail="订单已过期，请重新下单")
            if _order_has_payment_entry(existing):
                return _order_to_dict(existing)
            order = existing
            order_no = existing.order_no
            # A retry must charge the amount captured by the original local
            # reservation, even if an operator changed the current price.
            amount_fen = int(existing.amount_fen)
    if not existing:
        order_no = f"CS{int(time.time())}{uuid.uuid4().hex[:10].upper()}"
        order_kwargs: dict[str, Any] = {
            "order_no": order_no,
            "user_id": current_user.id,
            "amount_fen": amount_fen,
            "method": method,
            "plan": body.plan,
        }
        if key and hasattr(PaymentOrder, "idempotency_key"):
            order_kwargs["idempotency_key"] = key
        expires_at = _order_expire_at()
        if expires_at is not None:
            order_kwargs["expires_at"] = expires_at
        order = PaymentOrder(**order_kwargs)
        db.add(order)
        try:
            # Commit the reservation before contacting GGGUA.  If the upstream
            # accepts the order but our response/commit is interrupted, a
            # retry with the same Idempotency-Key can reuse this out_trade_no
            # instead of creating a second provider order.
            db.commit()
            db.refresh(order)
        except IntegrityError:
            db.rollback()
            if key and hasattr(PaymentOrder, "idempotency_key"):
                existing = db.query(PaymentOrder).filter(
                    PaymentOrder.user_id == current_user.id,
                    PaymentOrder.idempotency_key == key,
                ).first()
                if existing:
                    # The unique-key race can happen after the initial lookup
                    # (two requests may both observe no row).  Re-apply the
                    # same payload binding here; otherwise a concurrent
                    # request using the same key for a different method could
                    # receive and display the other checkout's order.
                    if _normalise_method(existing.method) != method or existing.plan != body.plan:
                        raise HTTPException(status_code=409, detail="幂等键已用于其他订单")
                    if existing.status != "pending" or _order_has_payment_entry(existing):
                        return _order_to_dict(existing)
                    # The winner may have crashed after reserving the local row
                    # but before saving the provider response.  Continue with
                    # this durable reservation so a retry can recover the same
                    # GGGUA out_trade_no instead of leaving a permanently empty
                    # pending order.  Mirror the normal existing-order path's
                    # expiry guard before contacting the provider.
                    if _is_expired(existing):
                        await _reconcile_order_from_provider(
                            db, existing, allow_expired=True
                        )
                        db.refresh(existing)
                        if existing.status != "pending":
                            return _order_to_dict(existing)
                        raise HTTPException(status_code=409, detail="订单已过期，请重新下单")
                    order = existing
                    order_no = existing.order_no
                    amount_fen = int(existing.amount_fen)
            if not existing:
                raise HTTPException(status_code=503, detail="订单暂时无法创建，请稍后重试")

    provider_result: dict[str, Any]
    try:
        if dev_mode:
            provider_result = _mock_payment_result(order_no)
        else:
            client_ip = _request_client_ip(request)
            provider_result = await _create_gggua_payment(
                order_no,
                _amount_yuan(amount_fen),
                method,
                client_ip=client_ip,
            )
        provider_trade_no = provider_result.get("trade_no")
        if provider_trade_no:
            provider_trade_no = str(provider_trade_no)
            saved_trade_no = str(order.transaction_id or "").strip()
            if saved_trade_no and saved_trade_no != provider_trade_no:
                raise PaymentProviderError("GGGUA 返回的第三方流水号与本地订单不一致")
            order.transaction_id = provider_trade_no
        order.pay_url = provider_result.get("pay_url")
        order.qr_code_url = provider_result.get("qr_code_url")
        if hasattr(order, "qr_payload"):
            order.qr_payload = provider_result.get("qr_payload") or provider_result.get("qrcode")
        if hasattr(order, "url_scheme"):
            order.url_scheme = provider_result.get("urlscheme")
        db.commit()
        db.refresh(order)
    except (PaymentConfigurationError, PaymentProviderError) as exc:
        # Keep the durable pending reservation.  A subsequent request with the
        # same key can retry the same provider out_trade_no safely.
        db.rollback()
        if isinstance(exc, PaymentConfigurationError):
            raise HTTPException(
                status_code=503,
                detail="支付暂不可用，请联系管理员配置 GGGUA 商户参数",
            )
        logger.exception("gggua create order failed")
        raise HTTPException(status_code=503, detail="支付服务暂时不可用，请稍后重试")
    except IntegrityError:
        db.rollback()
        logger.exception("gggua order reservation update failed")
        raise HTTPException(status_code=503, detail="订单暂时无法完成，请稍后重试")

    result = _order_to_dict(order)
    result.update(
        {
            "provider": "gggua",
            "qrcode": provider_result.get("qrcode"),
            "urlscheme": provider_result.get("urlscheme"),
            "qr_payload": provider_result.get("qr_payload"),
            "qr_code_is_url": bool(provider_result.get("qr_code_is_url", False)),
        }
    )
    return result


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(PaymentOrder).filter(
        PaymentOrder.id == order_id,
        PaymentOrder.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "pending":
        # Even after the local checkout window, ask GGGUA once before closing
        # the order.  A successful payment can race the asynchronous callback;
        # closing first would acknowledge the callback while silently dropping
        # the user's subscription.
        await _reconcile_order_from_provider(
            db, order, allow_expired=_is_expired(order)
        )
        # The reconciliation helper may have committed through a locked
        # instance; refresh the object used for the response.  Keep an unpaid
        # expired row pending here: a local timeout must not turn a late,
        # legitimate GGGUA callback into an acknowledged-but-unsettled payment.
        # New attempts are still blocked by the idempotency check above, and
        # the frontend's checkout timeout presents the expired state to users.
        db.refresh(order)
    return _order_to_dict(order)


def _notify_failure() -> PlainTextResponse:
    # Any response other than the exact lowercase ``success`` tells GGGUA to
    # retry.  Keep failures as plain text too, so no framework JSON leaks into
    # the payment protocol.
    return PlainTextResponse("fail", status_code=400)


async def _read_notify_params(request: Request) -> dict[str, str]:
    query_items = [(str(k), str(v)) for k, v in request.query_params.multi_items()]
    seen_keys: set[str] = set()
    for key, _ in query_items:
        lowered = key.lower()
        if lowered in seen_keys:
            return {}
        seen_keys.add(lowered)
    params = dict(query_items)
    if request.method.upper() == "GET":
        return params
    try:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            body = await request.json()
        else:
            # Keep FormData's multi_items() so duplicate signed fields are
            # rejected instead of silently collapsed by ``dict(form)``.
            body = await request.form()
    except (ValueError, TypeError, UnicodeDecodeError):
        return {}
    if isinstance(body, Mapping):
        body_items = (
            [(str(k), str(v)) for k, v in body.multi_items() if v is not None]
            if hasattr(body, "multi_items")
            else [(str(k), str(v)) for k, v in body.items() if v is not None]
        )
        body_params: dict[str, str] = {}
        body_seen: set[str] = set()
        for key, value in body_items:
            lowered = key.lower()
            if lowered in body_seen or lowered in seen_keys:
                return {}
            body_seen.add(lowered)
            body_params[key] = value
        if len(body_seen) != len(body_params):
            return {}
        body_params.update(params)
        return body_params
    return params


async def _handle_gggua_notify(
    params: Mapping[str, Any], db: Session
) -> PlainTextResponse:
    if not _gggua_is_configured():
        raise HTTPException(status_code=503, detail="支付回调验签参数未配置")
    if not _verify_gggua_sign(params):
        return _notify_failure()
    expected_pid = str(_setting("gggua_pid", "") or "").strip()
    callback_pid = _single_value(params, "pid")
    if callback_pid != expected_pid:
        return _notify_failure()
    trade_status = (_single_value(params, "trade_status", "tradeStatus") or "").upper()
    if trade_status != "TRADE_SUCCESS":
        return _notify_failure()
    order_no = _single_value(params, "out_trade_no", "outTradeNo")
    if not order_no or len(order_no) > 64:
        return _notify_failure()

    callback_type = (_single_value(params, "type") or "").lower()
    if callback_type not in set(GGGUA_METHODS.values()):
        return _notify_failure()
    transaction_id = _single_value(
        params, "trade_no", "tradeNo", "transaction_id"
    )
    if not transaction_id or len(transaction_id) > 100:
        return _notify_failure()
    callback_money = _single_value(params, "money")
    callback_fen = _money_to_fen(callback_money)
    if callback_fen is None:
        return _notify_failure()

    # Lock before checking local state/amount/provider ID.  MySQL serializes
    # duplicate notifications here; the conditional UPDATE in
    # ``_mark_order_paid`` is the final pending->paid gate for SQLite and
    # multi-worker deployments where SELECT .. FOR UPDATE is unavailable.
    order = db.query(PaymentOrder).filter(
        PaymentOrder.order_no == order_no
    ).with_for_update().first()
    if not order:
        # Ask GGGUA to retry.  A valid payment for an unknown local order is a
        # deployment/data-integrity incident and must not be silently acked.
        return _notify_failure()

    expected_type = GGGUA_METHODS.get(_normalise_method(order.method))
    if not expected_type or callback_type != expected_type:
        return _notify_failure()
    if callback_fen != int(order.amount_fen):
        return _notify_failure()
    saved_transaction_id = str(order.transaction_id or "").strip()
    # GGGUA can deliver the callback before the response from mapi.php has
    # been committed locally.  An empty local transaction_id is therefore a
    # valid first notification; only a conflicting already-saved ID is invalid.
    if saved_transaction_id and transaction_id != saved_transaction_id:
        return _notify_failure()
    currency = (_single_value(params, "currency") or "").upper()
    if currency and currency not in {"CNY", "RMB"}:
        return _notify_failure()

    # Idempotency is evaluated only after all signed business fields match the
    # original order.  A forged/malformed repeat must never receive success.
    if order.status == "paid":
        return PlainTextResponse("success")
    if order.status == "refunded":
        return PlainTextResponse("success")
    if order.status == "closed":
        # A local close is not proof that GGGUA did not settle the order.  Do
        # not acknowledge a late TRADE_SUCCESS here: returning ``fail`` keeps
        # the provider retrying so the payment can be reconciled manually or
        # through a later callback instead of silently losing the entitlement.
        return _notify_failure()
    if order.status != "pending":
        return _notify_failure()
    duplicate = db.query(PaymentOrder.id).filter(
        PaymentOrder.transaction_id == transaction_id,
        PaymentOrder.id != order.id,
    ).first()
    if duplicate:
        return _notify_failure()

    try:
        # A signed TRADE_SUCCESS is authoritative even if the local checkout
        # expiry has passed; expiry only prevents creating/retrying a new
        # provider order with the same idempotency key.
        if not _mark_order_paid(
            db, order, transaction_id, allow_expired=True
        ):
            db.rollback()
            # A competing worker may have settled the same order after the
            # initial status check.  A paid/refunded row can be acknowledged;
            # anything else must be retried so a close/rollback race cannot
            # silently discard a legitimate payment.
            try:
                db.refresh(order)
            except Exception:
                return _notify_failure()
            if order.status in {"paid", "refunded"}:
                return PlainTextResponse("success")
            return _notify_failure()
        db.commit()
    except IntegrityError:
        db.rollback()
        return _notify_failure()
    return PlainTextResponse("success")


@router.api_route(
    "/notify", methods=["GET", "POST"], response_class=PlainTextResponse
)
async def gggua_notify(request: Request, db: Session = Depends(get_db)):
    """GGGUA GET 回调；保留 POST 兼容旧网关配置。"""
    params = await _read_notify_params(request)
    return await _handle_gggua_notify(params, db)


@router.post("/dev-pay/{order_id}")
def dev_pay(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _payment_dev_enabled():
        raise HTTPException(status_code=403, detail="开发模拟支付未启用")
    # ``with_for_update`` protects MySQL/PostgreSQL; the process lock covers
    # SQLite, whose dialect ignores row-level locks.  Keep the whole state
    # transition inside the critical section so a double click cannot extend
    # one subscription twice.
    with _dev_payment_lock:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.id == order_id,
            PaymentOrder.user_id == current_user.id,
        ).with_for_update().first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        if order.status == "paid":
            return {"status": "paid", "message": "订单已经支付，无需重复处理"}
        if order.status != "pending":
            raise HTTPException(status_code=409, detail="订单当前不可支付")
        if _is_expired(order):
            order.status = "closed"
            db.commit()
            raise HTTPException(status_code=409, detail="订单已过期，请重新下单")

        transaction_id = f"DEV_{order.id}_{uuid.uuid4().hex[:10].upper()}"
        if not _mark_order_paid(db, order, transaction_id):
            db.rollback()
            raise HTTPException(status_code=409, detail="订单当前不可支付")
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="订单当前不可支付")
        return {"status": "paid", "message": "模拟支付成功，订阅已激活"}
