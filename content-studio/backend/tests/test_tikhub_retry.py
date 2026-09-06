import ssl
import unittest
from unittest.mock import patch

import httpx

from services.tikhub import TikHubClient, TikHubRequestError


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.headers = {}
        self._payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.tikhub.io/test")
            raise httpx.HTTPStatusError("upstream failure", request=request, response=self)

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(self, outcomes, *args, **kwargs):
        self._outcomes = outcomes

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, *args, **kwargs):
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class TikHubRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_douyin_user_search_uses_current_post_endpoint(self):
        calls = []
        client = TikHubClient()

        async def fake_post(endpoint, json_data=None):
            calls.append((endpoint, json_data))
            return {"data": {"user_list": []}}

        with patch.object(client, "_post", side_effect=fake_post):
            result = await client.douyin_search_users("测试", count=10)

        self.assertEqual(result, {"data": {"user_list": []}})
        self.assertEqual(calls, [(
            "/api/v1/douyin/search/fetch_user_search",
            {
                "keyword": "测试",
                "cursor": 0,
                "douyin_user_fans": "",
                "douyin_user_type": "",
                "search_id": "",
            },
        )])

    async def test_douyin_sec_uid_profile_uses_current_endpoint(self):
        with patch.object(
            client := TikHubClient(),
            "_get",
            return_value={"data": {"user_info": {}}},
        ) as get:
            result = await client.douyin_get_user_by_sec_uid("sec-uid")

        self.assertEqual(result, {"data": {"user_info": {}}})
        get.assert_awaited_once_with(
            "/api/v1/douyin/web/handler_user_profile",
            {"sec_user_id": "sec-uid"},
        )

    async def test_ssl_eof_retries_with_a_fresh_client(self):
        outcomes = [ssl.SSLError("UNEXPECTED_EOF_WHILE_READING"), _Response()]
        client = TikHubClient()
        client.max_retries = 1
        client.retry_backoff = 0

        with patch(
            "services.tikhub.httpx.AsyncClient",
            side_effect=lambda *args, **kwargs: _FakeAsyncClient(outcomes, *args, **kwargs),
        ) as factory:
            result = await client._get("/test")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(outcomes, [])

    async def test_exhausted_transport_retries_have_safe_message(self):
        outcomes = [ssl.SSLError("UNEXPECTED_EOF_WHILE_READING")] * 3
        client = TikHubClient()
        client.max_retries = 2
        client.retry_backoff = 0

        with patch(
            "services.tikhub.httpx.AsyncClient",
            side_effect=lambda *args, **kwargs: _FakeAsyncClient(outcomes, *args, **kwargs),
        ) as factory:
            with self.assertRaises(TikHubRequestError) as ctx:
                await client._get("/test")

        self.assertIn("TLS 连接被上游中断", str(ctx.exception))
        self.assertIn("已重试 2 次", str(ctx.exception))
        self.assertEqual(factory.call_count, 3)

    async def test_client_error_is_not_retried(self):
        outcomes = [_Response(status_code=400)]
        client = TikHubClient()
        client.max_retries = 3
        client.retry_backoff = 0

        with patch(
            "services.tikhub.httpx.AsyncClient",
            side_effect=lambda *args, **kwargs: _FakeAsyncClient(outcomes, *args, **kwargs),
        ) as factory:
            with self.assertRaises(httpx.HTTPStatusError):
                await client._get("/test")

        self.assertEqual(factory.call_count, 1)


if __name__ == "__main__":
    unittest.main()
