"""HTTPS-only fetches whose redirect policy preserves the original trust boundary."""
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener


def validate_url(url: str, allowed_hosts) -> None:
    parsed = urlparse(url)
    if (parsed.scheme != 'https' or parsed.hostname not in allowed_hosts
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443)):
        raise URLError('Refusing URL outside the allowed HTTPS origin')


class TrustedRedirects(HTTPRedirectHandler):
    def __init__(self, allowed_hosts):
        super().__init__()
        self.allowed_hosts = frozenset(allowed_hosts)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_trusted(request, allowed_hosts, timeout):
    validate_url(request.full_url, allowed_hosts)
    return build_opener(TrustedRedirects(allowed_hosts)).open(request, timeout=timeout)
