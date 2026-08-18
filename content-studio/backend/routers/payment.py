"""
支付路由：基于 YunGouOS 聚合支付（微信/支付宝/一码付）
文档: https://open.pay.yungouos.com/
"""
import uuid
import time
import hashlib
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User, Subscription, PaymentOrder
from config import settings
from .deps import get_current_user

router = APIRouter(prefix="/payment", tags=["payment"])

YUNGOUOS_BASE = "https://api.pay.yungouos.com/api/pay"


# -- 签名工具 --

def _yungouos_sign(params: dict) -> str:
    """
    YunGouOS 签名算法：
    1. 过滤空值和 sign 字段
    2. 按 key ASCII 升序排列
    3. 拼接 key=value& 格式
    4. 末尾追加 &key=商户密钥
    5. MD5 后转大写
    """
    filtered = {k: v for k, v in params.items() if v not in (None, "") and k != "sign"}
    sorted_str = "&".join(f"{k}={filtered[k]}" for k in sorted(filtered.keys()))
    sign_str = f"{sorted_str}&key={settings.yungouos_key}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()


def _verify_notify_sign(params: dict) -> bool:
    """验证 YunGouOS 回调签名"""
    sign = params.get("sign", "")
    if not sign:
        return False
    expected = _yungouos_sign(params)
    return sign == expected


# -- Pydantic --

class CreateOrderRequest(BaseModel):
    method: str = "wechat"    # wechat / alipay / merge
    plan: str = "monthly"


# -- YunGouOS 下单 --

async def _create_wxpay_native(order_no: str, amount_yuan: str, body_text: str) -> str:
    """微信扫码支付，返回二维码图片 URL"""
    params = {
        "out_trade_no": order_no,
        "total_fee": amount_yuan,
        "mch_id": settings.yungouos_wxpay_mchid,
        "body": body_text,
    }
    params["sign"] = _yungouos_sign(params)
    # 签名后追加非签名参数
    params["type"] = "2"  # 返回二维码图片地址
    if settings.yungouos_notify_url:
        params["notify_url"] = settings.yungouos_notify_url

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{YUNGOUOS_BASE}/wxpay/nativePay", data=params)
        data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"YunGouOS 微信下单失败: {data.get('msg', data)}")
    return data["data"]


async def _create_alipay_native(order_no: str, amount_yuan: str, body_text: str) -> str:
    """支付宝扫码支付，返回二维码图片 URL"""
    params = {
        "out_trade_no": order_no,
        "total_fee": amount_yuan,
        "mch_id": settings.yungouos_alipay_mchid,
        "body": body_text,
    }
    params["sign"] = _yungouos_sign(params)
    params["type"] = "2"
    if settings.yungouos_notify_url:
        params["notify_url"] = settings.yungouos_notify_url

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{YUNGOUOS_BASE}/alipay/nativePay", data=params)
        data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"YunGouOS 支付宝下单失败: {data.get('msg', data)}")
    return data["data"]


async def _create_merge_native(order_no: str, amount_yuan: str, body_text: str) -> str:
    """聚合一码付（微信+支付宝自动识别），返回二维码图片 URL"""
    params = {
        "out_trade_no": order_no,
        "total_fee": amount_yuan,
        "mch_id": settings.yungouos_merge_mchid,
        "body": body_text,
    }
    params["sign"] = _yungouos_sign(params)
    params["type"] = "2"
    if settings.yungouos_notify_url:
        params["notify_url"] = settings.yungouos_notify_url

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{YUNGOUOS_BASE}/merge/nativePay", data=params)
        data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"YunGouOS 聚合下单失败: {data.get('msg', data)}")
    return data["data"]


# -- 端点 --

@router.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建支付订单，返回二维码图片 URL"""
    if body.plan != "monthly":
        raise HTTPException(status_code=400, detail="暂只支持月度套餐")
    if body.method not in ("wechat", "alipay", "merge"):
        raise HTTPException(status_code=400, detail="method 须为 wechat、alipay 或 merge")

    amount_fen = settings.monthly_price_fen
    amount_yuan = f"{amount_fen / 100:.2f}"
    order_no = f"CS{int(time.time())}{uuid.uuid4().hex[:8].upper()}"
    description = "文策引擎 标准版 · 1个月"

    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        amount_fen=amount_fen,
        method=body.method,
        plan=body.plan,
    )

    try:
        if body.method == "wechat":
            qr_url = await _create_wxpay_native(order_no, amount_yuan, description)
        elif body.method == "alipay":
            qr_url = await _create_alipay_native(order_no, amount_yuan, description)
        else:
            qr_url = await _create_merge_native(order_no, amount_yuan, description)
        order.qr_code_url = qr_url
    except RuntimeError as e:
        if settings.debug:
            order.qr_code_url = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=DEV_MOCK"
        else:
            raise HTTPException(status_code=503, detail=str(e))

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "amount_fen": order.amount_fen,
        "method": order.method,
        "qr_code_url": order.qr_code_url,
        "status": order.status,
    }


@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """前端轮询：查询订单状态"""
    order = db.query(PaymentOrder).filter(
        PaymentOrder.id == order_id,
        PaymentOrder.user_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_id": order.id,
        "status": order.status,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


@router.post("/notify")
async def yungouos_notify(request: Request, db: Session = Depends(get_db)):
    """
    YunGouOS 异步回调通知
    POST form-urlencoded:
      code, orderNo, outTradeNo, payNo, money, mchId, sign
    code=1 表示支付成功
    """
    form = await request.form()
    params = {k: v for k, v in form.items()}

    if not _verify_notify_sign(params):
        return "FAIL"

    code = params.get("code")
    out_trade_no = params.get("outTradeNo", "")
    pay_no = params.get("payNo", "")

    if str(code) == "1" and out_trade_no:
        order = db.query(PaymentOrder).filter(PaymentOrder.order_no == out_trade_no).first()
        if not order:
            return "SUCCESS"

        # 幂等：已支付订单直接忽略重复通知
        if order.status == "paid":
            return "SUCCESS"

        # 幂等：支付流水号已处理过则直接成功返回，避免重复激活订阅
        if pay_no:
            existing_tx = db.query(PaymentOrder.id).filter(
                PaymentOrder.transaction_id == pay_no,
                PaymentOrder.status == "paid",
            ).first()
            if existing_tx:
                return "SUCCESS"

        paid_at = datetime.utcnow()
        updated = db.query(PaymentOrder).filter(
            PaymentOrder.id == order.id,
            PaymentOrder.status == "pending",
        ).update(
            {
                PaymentOrder.status: "paid",
                PaymentOrder.transaction_id: pay_no,
                PaymentOrder.paid_at: paid_at,
            },
            synchronize_session=False,
        )

        # 只有首次把 pending 改成 paid 的请求才会触发订阅激活
        if updated == 1:
            db.flush()
            _activate_subscription(db, order.user_id, order.plan)
            db.commit()

    return "SUCCESS"


# -- 订阅激活 --

def _activate_subscription(db: Session, user_id: int, plan: str):
    """支付成功后激活/续费订阅"""
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    now = datetime.utcnow()

    if plan == "monthly":
        duration = timedelta(days=30)
    else:
        duration = timedelta(days=30)

    if sub:
        base = sub.expire_at if sub.expire_at > now else now
        sub.plan = plan
        sub.expire_at = base + duration
        sub.is_active = True
        sub.updated_at = now
    else:
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            expire_at=now + duration,
        )
        db.add(sub)


# -- 开发模式模拟支付完成 --

@router.post("/dev-pay/{order_id}")
def dev_pay(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开发专用：直接将订单标记为已支付并激活订阅"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="仅开发模式可用")

    import os
    if os.environ.get("DISABLE_DEV_PAY", "").lower() in ("1", "true", "yes"):
        raise HTTPException(status_code=403, detail="dev-pay 已被禁用")

    order = db.query(PaymentOrder).filter(
        PaymentOrder.id == order_id,
        PaymentOrder.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.status = "paid"
    order.transaction_id = f"DEV_{uuid.uuid4().hex[:12].upper()}"
    order.paid_at = datetime.utcnow()
    db.flush()
    _activate_subscription(db, order.user_id, order.plan)
    db.commit()

    return {"status": "paid", "message": "模拟支付成功，订阅已激活"}
