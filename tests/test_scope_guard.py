import unittest

from bugintel.core.scope_guard import TargetScope


class TestScopeGuard(unittest.TestCase):
    def setUp(self):
        self.scope = TargetScope(
            target_name="demo-lab",
            allowed_domains=["demo.example.com", "*.demo.example.com"],
            allowed_schemes=["https"],
            allowed_methods=["GET", "HEAD", "OPTIONS"],
            forbidden_paths=["/logout", "/delete*"],
        )

    def test_allows_exact_domain(self):
        decision = self.scope.is_url_allowed("https://demo.example.com/api/users", "GET")
        self.assertTrue(decision.allowed)

    def test_allows_subdomain_wildcard(self):
        decision = self.scope.is_url_allowed("https://api.demo.example.com/v1/me", "GET")
        self.assertTrue(decision.allowed)

    def test_blocks_out_of_scope_domain(self):
        decision = self.scope.is_url_allowed("https://evil.example.net/api/users", "GET")
        self.assertFalse(decision.allowed)
        self.assertIn("Domain not in scope", decision.reason)

    def test_blocks_http_scheme(self):
        decision = self.scope.is_url_allowed("http://demo.example.com/api/users", "GET")
        self.assertFalse(decision.allowed)
        self.assertIn("Scheme not allowed", decision.reason)

    def test_blocks_write_method(self):
        decision = self.scope.is_url_allowed("https://demo.example.com/api/users", "POST")
        self.assertFalse(decision.allowed)
        self.assertIn("HTTP method not allowed", decision.reason)

    def test_blocks_forbidden_path(self):
        decision = self.scope.is_url_allowed("https://demo.example.com/logout", "GET")
        self.assertFalse(decision.allowed)
        self.assertIn("Path is forbidden", decision.reason)


if __name__ == "__main__":
    unittest.main()
