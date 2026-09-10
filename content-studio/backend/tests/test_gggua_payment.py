"""GGGUA V1 adapter regression tests; no network calls or real credentials."""

import hashlib
import asyncio
import logging
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from logging_utils import SensitiveQueryFilter
from routers.payment import (
    CreateOrderRequest,
    PaymentProviderError,
    _handle_gggua_notify,
    _mark_order_paid,
    _monthly_price_fen,
    _reconcile_order_from_provider,
    _gggua_sign,
    _money_to_fen,
    _parse_gggua_create_response,
    _query_result_is_paid,
    _request_client_ip,
    _verify_gggua_sign,
    create_order,
)
from database import Base
from models import PaymentOrder, Tenant, User


class GgguaPaymentUnitTests(unittest.TestCase):
    def test_http_query_logs_redact_provider_key(self):
        record = logging.LogRecord(
            "httpx",
            logging.INFO,
            __file__,
            1,
            "HTTP Request: GET https://pay.gggua.com/api.php?act=order&key=%s&out_trade_no=x",
            ("test-secret",),
            None,
        )
        self.assertTrue(SensitiveQueryFilter().filter(record))
        rendered = record.getMessage()
        self.assertNotIn("test-secret", rendered)
        self.assertIn("key=<redacted>", rendered)

    def test_md5_vector_uses_raw_values_and_appends_key_directly(self):
        params = {
            "type": "alipay",
            "money": "49.00",
            "pid": "1001",
            "notify_url": "https://example.test/api/payment/notify?a=1&b=2",
            "param": "",
            "sign_type": "MD5",
            "sign": "ignored",
        }
        expected_raw = (
            "money=49.00&notify_url=https://example.test/api/payment/notify?a=1&b=2"
            "&pid=1001&type=alipaysecret"
        )
        with patch.object(settings, "gggua_key", "secret"):
            self.assertEqual(
                _gggua_sign(params),
                hashlib.md5(expected_raw.encode("utf-8")).hexdigest(),
            )

    def test_callback_signature_requires_configured_key_and_md5(self):
        params = {
            "pid": "1001",
            "type": "wxpay",
            "out_trade_no": "CS1",
            "money": "49.00",
            "trade_status": "TRADE_SUCCESS",
            "sign_type": "MD5",
        }
        with patch.object(settings, "gggua_key", "secret"), patch.object(
            settings, "gggua_pid", "1001"
        ):
            signed = {**params, "sign": _gggua_sign(params)}
            self.assertTrue(_verify_gggua_sign(signed))
            self.assertFalse(_verify_gggua_sign({**signed, "sign_type": "SHA256"}))
        with patch.object(settings, "gggua_key", ""):
            self.assertFalse(_verify_gggua_sign(signed))

    def test_signing_normalises_operator_key_whitespace(self):
        params = {"pid": "1001", "money": "49.00"}
        with patch.object(settings, "gggua_key", "  secret  "):
            self.assertEqual(_gggua_sign(params), _gggua_sign(params, "secret"))

    def test_money_parser_rejects_float_traps_and_exponents(self):
        self.assertEqual(_money_to_fen("49"), 4900)
        self.assertEqual(_money_to_fen("49.0"), 4900)
        self.assertEqual(_money_to_fen("49.00"), 4900)
        for value in ("49.001", "4.9e1", "NaN", "Infinity", "-1", "", "9" * 21):
            with self.subTest(value=value):
                self.assertIsNone(_money_to_fen(value))

    def test_invalid_monthly_price_fails_closed(self):
        with patch.object(settings, "monthly_price_fen", "not-a-number"):
            self.assertEqual(_monthly_price_fen(), 0)

    def test_provider_response_requires_exactly_one_entry_point(self):
        base = {"code": 1, "trade_no": "T1"}
        for field in ("payurl", "qrcode", "urlscheme"):
            with self.subTest(field=field):
                result = _parse_gggua_create_response({**base, field: "value"})
                self.assertEqual(result[field], "value")
        scheme = _parse_gggua_create_response({**base, "urlscheme": "weixin://pay"})
        self.assertIsNone(scheme["qr_payload"])
        with self.assertRaises(PaymentProviderError):
            _parse_gggua_create_response({**base, "payurl": "a", "qrcode": "b"})
        with self.assertRaises(PaymentProviderError):
            _parse_gggua_create_response(base)
        with self.assertRaises(PaymentProviderError):
            _parse_gggua_create_response({**base, "qrcode": "x" * 4097})

    def test_forwarded_client_ip_uses_nearest_non_proxy_hop(self):
        request = SimpleNamespace(
            client=SimpleNamespace(host="127.0.0.1"),
            headers={"x-forwarded-for": "198.51.100.7, 127.0.0.1"},
        )
        with patch.object(settings, "gggua_client_ip", ""), patch.object(
            settings, "payment_trusted_proxy_ips", "127.0.0.1"
        ):
            self.assertEqual(_request_client_ip(request), "198.51.100.7")


class GggguaNotifyTests(unittest.TestCase):
    """回调必须同时满足签名、订单业务字段和幂等约束。"""

    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        tenant = Tenant(name="payment-test")
        user = User(email="payment@example.test", tenant=tenant)
        self.db.add_all([tenant, user])
        self.db.commit()
        self.user = user
        self.order = PaymentOrder(
            order_no="CS_NOTIFY_1",
            user_id=user.id,
            amount_fen=4900,
            method="wechat",
            plan="monthly",
            status="pending",
            transaction_id="GGGUA_TRADE_1",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        self.db.add(self.order)
        self.db.commit()
        self.db.refresh(self.order)
        self.settings_patch = patch.multiple(
            settings,
            payment_provider="gggua",
            gggua_pid="1001",
            gggua_key="test-secret",
            gggua_notify_url="https://example.test/api/payment/notify",
            gggua_base_url="https://pay.gggua.com",
            gggua_api_base="https://pay.gggua.com",
            debug=False,
        )
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()
        self.db.close()
        self.engine.dispose()

    def callback(self, **overrides):
        params = {
            "pid": "1001",
            "trade_no": "GGGUA_TRADE_1",
            "out_trade_no": "CS_NOTIFY_1",
            "type": "wxpay",
            "name": "文策引擎",
            "money": "49.00",
            "trade_status": "TRADE_SUCCESS",
            "sign_type": "MD5",
        }
        params.update(overrides)
        params["sign"] = _gggua_sign(params)
        return params

    def test_valid_callback_activates_subscription_and_is_idempotent(self):
        first = asyncio.run(_handle_gggua_notify(self.callback(), self.db))
        self.assertEqual(first.body, b"success")
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, "paid")
        self.assertIsNotNone(self.user.subscription)
        first_expiry = self.user.subscription.expire_at

        second = asyncio.run(_handle_gggua_notify(self.callback(), self.db))
        self.assertEqual(second.body, b"success")
        self.db.refresh(self.user.subscription)
        self.assertEqual(self.user.subscription.expire_at, first_expiry)

    def test_atomic_paid_transition_allows_only_one_stale_worker(self):
        # Load the same pending row into two independent sessions before the
        # first worker commits.  SQLite ignores SELECT .. FOR UPDATE, so this
        # models the stale-object race that can occur across workers.
        second_db = self.Session()
        try:
            first_order = self.db.query(PaymentOrder).filter(
                PaymentOrder.id == self.order.id
            ).first()
            second_order = second_db.query(PaymentOrder).filter(
                PaymentOrder.id == self.order.id
            ).first()
            self.assertTrue(_mark_order_paid(self.db, first_order, "TX_ATOMIC_1"))
            self.db.commit()
            self.assertFalse(_mark_order_paid(second_db, second_order, "TX_ATOMIC_1"))
            second_db.rollback()
            self.db.refresh(self.order)
            self.assertEqual(self.order.status, "paid")
            self.db.refresh(self.user.subscription)
            self.assertEqual(
                self.user.subscription.expire_at,
                self.user.subscription.started_at + timedelta(days=30),
            )
        finally:
            second_db.close()

    def test_callback_rejects_mismatched_business_fields_before_paid_shortcut(self):
        asyncio.run(_handle_gggua_notify(self.callback(money="0.01"), self.db))
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, "pending")

        self.order.status = "paid"
        self.db.commit()
        response = asyncio.run(_handle_gggua_notify(self.callback(type="alipay"), self.db))
        self.assertEqual(response.body, b"fail")

    def test_provider_query_fallback_reconciles_a_late_callback(self):
        from routers import payment as payment_router

        query_result = {
            "code": 1,
            "trade_no": "GGGUA_TRADE_1",
            "out_trade_no": "CS_NOTIFY_1",
            "type": "wxpay",
            "money": "49.00",
            "status": 1,
        }
        with patch.object(settings, "payment_query_fallback", True), patch.object(
            settings, "payment_query_interval_seconds", 1
        ), patch.object(
            payment_router, "_query_gggua_order", new=AsyncMock(return_value=query_result)
        ):
            payment_router._provider_query_last_at.clear()
            asyncio.run(_reconcile_order_from_provider(self.db, self.order))
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, "paid")

    def test_provider_query_accepts_equivalent_status_aliases(self):
        result = {
            "code": 1,
            "status": 1,
            "trade_status": "TRADE_SUCCESS",
            "trade_no": "GGGUA_TRADE_1",
            "out_trade_no": "CS_NOTIFY_1",
            "type": "wxpay",
            "money": "49.00",
        }
        self.assertEqual(_query_result_is_paid(result, self.order), "GGGUA_TRADE_1")

        contradictory = {**result, "trade_status": "WAIT"}
        self.assertIsNone(_query_result_is_paid(contradictory, self.order))

    def test_reconcile_does_not_autoflush_dirty_transaction_before_lock(self):
        """A dirty ORM trade number must not escape as an autoflush 500."""
        from routers import payment as payment_router

        conflict = PaymentOrder(
            order_no="CS_NOTIFY_CONFLICT",
            user_id=self.user.id,
            amount_fen=4900,
            method="wechat",
            plan="monthly",
            status="pending",
            transaction_id="CONFLICT_TX",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        self.db.add(conflict)
        self.db.commit()

        # Leave the original row dirty in this Session.  With normal
        # autoflush, the subsequent lock query would attempt this conflicting
        # UPDATE before reconciliation's IntegrityError handler is entered.
        self.order.transaction_id = "CONFLICT_TX"
        query_result = {
            "code": 1,
            "trade_no": "CONFLICT_TX",
            "out_trade_no": "CS_NOTIFY_1",
            "type": "wxpay",
            "money": "49.00",
            "status": 1,
        }
        with patch.object(settings, "payment_query_fallback", True), patch.object(
            settings, "payment_query_interval_seconds", 1
        ), patch.object(
            payment_router, "_query_gggua_order", new=AsyncMock(return_value=query_result)
        ):
            payment_router._provider_query_last_at.clear()
            # The duplicate provider transaction is rejected and logged; the
            # route must not raise an unhandled autoflush IntegrityError.
            asyncio.run(_reconcile_order_from_provider(self.db, self.order))

        self.db.refresh(self.order)
        self.assertEqual(self.order.status, "pending")
        self.assertEqual(self.order.transaction_id, "GGGUA_TRADE_1")
        self.assertEqual(conflict.transaction_id, "CONFLICT_TX")

    def test_callback_can_set_transaction_id_when_provider_races_create_commit(self):
        self.order.transaction_id = None
        self.order.expires_at = datetime.utcnow() - timedelta(minutes=1)
        self.db.commit()
        response = asyncio.run(_handle_gggua_notify(self.callback(), self.db))
        self.assertEqual(response.body, b"success")
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.order.transaction_id, "GGGUA_TRADE_1")

    def test_late_callback_for_closed_order_is_not_acknowledged(self):
        self.order.status = "closed"
        self.db.commit()
        response = asyncio.run(_handle_gggua_notify(self.callback(), self.db))
        self.assertEqual(response.body, b"fail")
        self.assertEqual(response.status_code, 400)

    def test_callback_claim_race_retries_when_order_was_not_settled(self):
        with patch("routers.payment._mark_order_paid", return_value=False):
            response = asyncio.run(_handle_gggua_notify(self.callback(), self.db))
        self.assertEqual(response.body, b"fail")
        self.assertEqual(response.status_code, 400)

    def test_expired_idempotent_order_never_calls_provider_again(self):
        from routers import payment as payment_router
        from fastapi import HTTPException

        expired = PaymentOrder(
            order_no="CS_EXPIRED_1",
            user_id=self.user.id,
            amount_fen=4900,
            method="wechat",
            plan="monthly",
            status="pending",
            idempotency_key="checkout-expired",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        self.db.add(expired)
        self.db.commit()
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={})
        with patch.object(payment_router, "_create_gggua_payment", new=AsyncMock()) as provider:
            with patch.object(settings, "payment_query_fallback", False):
                with self.assertRaises(HTTPException) as raised:
                    asyncio.run(
                        create_order(
                            CreateOrderRequest(method="wechat", plan="monthly"),
                            request,
                            current_user=self.user,
                            db=self.db,
                            idempotency_key="checkout-expired",
                        )
                    )
        self.assertEqual(raised.exception.status_code, 409)
        provider.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
