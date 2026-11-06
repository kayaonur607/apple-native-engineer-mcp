"""Redirects must not leak App Store bearer tokens or escape Apple's origin."""
import unittest
from urllib.error import URLError
from urllib.request import Request
from support import TOOLS
from apple_native.http import TrustedRedirects, validate_url


class TrustedHTTPTests(unittest.TestCase):
    def test_rejects_untrusted_origins_and_plain_http(self):
        for url in ['http://developer.apple.com/a', 'https://evil.example/a',
                    'https://developer.apple.com:8443/a',
                    'https://user:secret@developer.apple.com/a']:
            with self.subTest(url=url), self.assertRaises(URLError):
                validate_url(url, {'developer.apple.com'})

    def test_redirect_is_checked_before_authorization_can_be_forwarded(self):
        handler = TrustedRedirects({'api.appstoreconnect.apple.com'})
        request = Request('https://api.appstoreconnect.apple.com/v1/apps',
                          headers={'Authorization': 'Bearer test-secret'})
        for url in ['https://attacker.example/steal', 'http://api.appstoreconnect.apple.com/v1/apps']:
            with self.subTest(url=url), self.assertRaises(URLError):
                handler.redirect_request(request, None, 302, 'Found', {}, url)
        safe = handler.redirect_request(request, None, 302, 'Found', {},
                                        'https://api.appstoreconnect.apple.com/v1/apps?page=2')
        self.assertEqual(safe.get_header('Authorization'), 'Bearer test-secret')
