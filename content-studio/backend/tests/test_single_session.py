import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException
from jose import jwt

from config import settings
from routers.deps import _ensure_session_token_fresh
from services.auth import create_jwt_token, decode_jwt_token


class SingleSessionTests(unittest.TestCase):
    def test_jwt_contains_session_version(self):
        token = create_jwt_token(user_id=123, session_version=7)

        token_data = decode_jwt_token(token)

        self.assertIsNotNone(token_data)
        self.assertEqual(token_data["user_id"], 123)
        self.assertEqual(token_data["session_version"], 7)

    def test_legacy_jwt_without_session_version_decodes_zero(self):
        legacy_payload = {
            "sub": "42",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        legacy_token = jwt.encode(
            legacy_payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        token_data = decode_jwt_token(legacy_token)

        self.assertIsNotNone(token_data)
        self.assertEqual(token_data["user_id"], 42)
        self.assertEqual(token_data["session_version"], 0)

    def test_stale_session_token_is_rejected(self):
        user = SimpleNamespace(session_version=5)

        with self.assertRaises(HTTPException) as err:
            _ensure_session_token_fresh(user, token_session_version=4)

        self.assertEqual(err.exception.status_code, 401)
        self.assertIn("其他设备登录", err.exception.detail)

    def test_current_session_token_is_allowed(self):
        user = SimpleNamespace(session_version=5)

        _ensure_session_token_fresh(user, token_session_version=5)


if __name__ == "__main__":
    unittest.main()
