import unittest

from routers import auth


class AuthRateLimitTests(unittest.TestCase):
    def setUp(self):
        auth._login_attempts.clear()

    def test_limit_triggers_after_max_failures(self):
        key = "127.0.0.1:user@example.com"
        for _ in range(auth._LOGIN_MAX_ATTEMPTS):
            auth._record_login_failure(key)

        retry_after = auth._check_login_rate_limit(key)
        self.assertGreater(retry_after, 0)

    def test_successful_clear_resets_limit_state(self):
        key = "127.0.0.1:user@example.com"
        auth._record_login_failure(key)
        auth._clear_login_attempts(key)

        retry_after = auth._check_login_rate_limit(key)
        self.assertEqual(retry_after, 0)


if __name__ == "__main__":
    unittest.main()
