import unittest

from main import app


class RouterContractTests(unittest.TestCase):
    def _has_route(self, method: str, path: str) -> bool:
        method = method.upper()
        for route in app.routes:
            methods = getattr(route, "methods", set()) or set()
            if route.path == path and method in methods:
                return True
        return False

    def test_key_api_routes_exist(self):
        expected_routes = [
            ("POST", "/api/auth/login"),
            ("POST", "/api/payment/orders"),
            ("GET", "/api/creators"),
            ("POST", "/api/creators/discover"),
            ("GET", "/api/documents"),
            ("POST", "/api/topics/search"),
            ("GET", "/api/style-templates"),
            ("POST", "/api/generate"),
            ("GET", "/api/generations"),
            ("GET", "/api/knowledge/stats"),
            ("POST", "/api/videos/{video_id}/analyze"),
            ("GET", "/api/viewpoints"),
            ("GET", "/api/image-proxy"),
        ]

        missing = [
            f"{method} {path}"
            for method, path in expected_routes
            if not self._has_route(method, path)
        ]
        self.assertEqual([], missing, f"Missing routes: {missing}")


if __name__ == "__main__":
    unittest.main()
