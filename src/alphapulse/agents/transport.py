"""Local-only Ollama transport with bounded responses and no redirects/proxies."""

import ipaddress
import json
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_RESPONSE_BYTES = 1024 * 1024


def local_endpoint(value):
    """Accept localhost or literal loopback addresses; reject URL credentials."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Ollama host must be a local HTTP endpoint")
    parsed = urlsplit(value if "://" in value else "http://" + value)
    try:
        port = parsed.port
        host = parsed.hostname
        local = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        local = False
    if (
        parsed.scheme != "http"
        or not local
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or port == 0
    ):
        raise ValueError(
            "Ollama host must be loopback HTTP without credentials or path"
        )
    return "http://" + parsed.netloc


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Ollama redirects are disabled")


def request_json(endpoint, path, payload=None):
    endpoint = local_endpoint(endpoint)
    if path not in ("/api/chat", "/api/tags", "/api/version"):
        raise ValueError("unsupported Ollama API path")
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(
        endpoint + path, data=data, headers={"Content-Type": "application/json"}
    )
    # Ignore HTTP_PROXY/HTTPS_PROXY so local fixture prompts cannot leave via proxy.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=120) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("Ollama response exceeds byte budget")
    return json.loads(body)
