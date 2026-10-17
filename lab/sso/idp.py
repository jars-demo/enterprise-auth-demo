"""A tiny OpenID Connect identity provider: the "Sign in with your company" side.

It knows three people in two companies (tenants), shows a login page, and implements the
authorization code flow with PKCE. Everything lives in memory; restart it to reset.
"""

import base64
import hashlib
import html
import json
import secrets
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .tokens import sign

KEY = b"workshop-only-signing-key-change-me"  # shared with the app; see tokens.py for why

USERS = {
    "alice": {"email": "alice@acme.test", "name": "Alice", "tenant": "acme", "roles": ["admin"]},
    "bob": {"email": "bob@acme.test", "name": "Bob", "tenant": "acme", "roles": ["viewer"]},
    "carol": {
        "email": "carol@globex.test",
        "name": "Carol",
        "tenant": "globex",
        "roles": ["admin"],
    },
}

# Registered apps. Redirect URIs must match exactly: no prefixes, no wildcards.
CLIENTS: dict[str, dict] = {}


class IdentityProvider(ThreadingHTTPServer):
    def __init__(self, port: int) -> None:
        super().__init__(("127.0.0.1", port), IdpHandler)
        self.issuer = f"http://127.0.0.1:{self.server_port}"
        self.codes: dict[str, dict] = {}


class IdpHandler(BaseHTTPRequestHandler):
    server: IdentityProvider

    def do_GET(self) -> None:
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/.well-known/openid-configuration":
            issuer = self.server.issuer
            self._json(
                200,
                {
                    "issuer": issuer,
                    "authorization_endpoint": f"{issuer}/authorize",
                    "token_endpoint": f"{issuer}/token",
                    "response_types_supported": ["code"],
                    "code_challenge_methods_supported": ["S256"],
                    "id_token_signing_alg_values_supported": ["HS256"],
                },
            )
        elif url.path == "/authorize":
            params = dict(urllib.parse.parse_qsl(url.query))
            problem = self._check_request(params)
            if problem:
                self._page(400, f"<p>Bad sign-in request: {html.escape(problem)}</p>")
            else:
                self._page(200, login_page(params))
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        form = dict(urllib.parse.parse_qsl(self._body()))
        path = urllib.parse.urlsplit(self.path).path
        if path == "/authorize":
            self._approve(form)
        elif path == "/token":
            self._token(form)
        else:
            self._json(404, {"error": "not_found"})

    def _check_request(self, params: dict) -> str | None:
        client = CLIENTS.get(params.get("client_id", ""))
        if not client:
            return "unknown client_id"
        if params.get("redirect_uri") not in client["redirect_uris"]:
            return "redirect_uri is not registered for this client"
        if params.get("response_type") != "code":
            return "only response_type=code is supported"
        if params.get("code_challenge_method") != "S256" or not params.get("code_challenge"):
            return "PKCE with S256 is required"
        return None

    def _approve(self, form: dict) -> None:
        # The user picked who they are on the login page. A real IdP checks a password, a
        # passkey or MFA here; that part is the IdP's job, never your app's.
        if self._check_request(form) or form.get("user") not in USERS:
            self._page(400, "<p>Bad sign-in request.</p>")
            return
        code = secrets.token_urlsafe(24)
        self.server.codes[code] = {
            "client_id": form["client_id"],
            "redirect_uri": form["redirect_uri"],
            "user": form["user"],
            "nonce": form.get("nonce"),
            "challenge": form["code_challenge"],
            "expires": time.time() + 60,
        }
        query = urllib.parse.urlencode({"code": code, "state": form.get("state", "")})
        self.send_response(302)
        self.send_header("Location", f"{form['redirect_uri']}?{query}")
        self.end_headers()

    def _token(self, form: dict) -> None:
        grant = self.server.codes.pop(form.get("code", ""), None)  # a code works only once
        client = CLIENTS.get(form.get("client_id", ""))
        if (
            not grant
            or not client
            or grant["expires"] < time.time()
            or grant["client_id"] != form.get("client_id")
            or grant["redirect_uri"] != form.get("redirect_uri")
            or not secrets.compare_digest(client["secret"], form.get("client_secret", ""))
        ):
            self._json(400, {"error": "invalid_grant"})
            return
        verifier = form.get("code_verifier", "")
        if pkce_challenge(verifier) != grant["challenge"]:
            self._json(400, {"error": "invalid_grant", "error_description": "PKCE failed"})
            return

        user = USERS[grant["user"]]
        now = int(time.time())
        common = {"iss": self.server.issuer, "sub": f"u-{grant['user']}", "iat": now}
        id_token = sign(
            {
                **common,
                "aud": grant["client_id"],
                "exp": now + 300,
                "nonce": grant["nonce"],
                "email": user["email"],
                "name": user["name"],
                "tenant": user["tenant"],
                "roles": user["roles"],
            },
            KEY,
        )
        access_token = sign({**common, "aud": "invoices-api", "exp": now + 300}, KEY)
        self._json(
            200,
            {
                "token_type": "Bearer",
                "expires_in": 300,
                "id_token": id_token,
                "access_token": access_token,
            },
        )

    def _body(self) -> str:
        length = min(int(self.headers.get("Content-Length") or 0), 10_000)
        return self.rfile.read(length).decode()

    def _json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _page(self, status: int, body: str) -> None:
        data = page("Acme Identity", body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        pass  # the app prints the flow; URLs here carry codes, so nothing is logged


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def login_page(params: dict) -> str:
    hidden = "".join(
        f'<input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">'
        for k, v in params.items()
    )
    buttons = "".join(
        f'<button name="user" value="{key}"><b>{html.escape(u["name"])}</b>'
        f"<span>{html.escape(u['email'])} · {u['tenant']} · {', '.join(u['roles'])}</span></button>"
        for key, u in USERS.items()
    )
    return (
        "<h1>Sign in</h1><p>Workshop identity provider. Pick who you are; a real one would ask"
        " for a password, a passkey or MFA.</p>"
        f"<form method=post action=/authorize>{hidden}{buttons}</form>"
    )


STYLE = "".join(
    [
        "body{font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:40px auto;",
        "padding:0 16px;color:#0b1f1e;}",
        "h1{font-size:28px;margin:0 0 8px;}",
        "code,pre{font:13px ui-monospace,monospace;}",
        "button{display:flex;flex-direction:column;align-items:flex-start;width:100%;",
        "margin:8px 0;padding:12px 16px;border:1px solid #cfdcda;border-radius:10px;",
        "background:#fff;cursor:pointer;font:inherit;text-align:left;}",
        "button:hover{border-color:#0f766e;}",
        "button span{color:#4b5f5d;font-size:14px;}",
        "table{width:100%;border-collapse:collapse;}",
        "td,th{padding:8px;border-bottom:1px solid #e3ebea;text-align:left;}",
        ".tag{display:inline-block;padding:2px 8px;border-radius:99px;background:#e6f4f1;",
        "color:#0f5e57;font-size:13px;}",
        "pre{white-space:pre-wrap;word-break:break-all;background:#f3f7f6;padding:12px;",
        "border-radius:8px;}",
        "a{color:#0f766e;}",
    ]
)


def page(title: str, body: str) -> str:
    return (
        f"<!doctype html><html lang=en><meta charset=utf-8>"
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{STYLE}</style><body>{body}</body></html>"
    )
