"""The app: "Sign in with SSO", a session, roles, and one tenant's invoices."""

import html
import json
import re
import secrets
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import store
from .idp import CLIENTS, KEY, page, pkce_challenge
from .rbac import can
from .tokens import TokenError, verify

CLIENT_ID = "invoices-app"


class App(ThreadingHTTPServer):
    def __init__(self, port: int, issuer: str, verbose: bool = True) -> None:
        super().__init__(("127.0.0.1", port), AppHandler)
        self.base = f"http://127.0.0.1:{self.server_port}"
        self.issuer = issuer
        self.verbose = verbose
        self.secret = secrets.token_urlsafe(24)
        self.logins: dict[str, dict] = {}  # state -> nonce and PKCE verifier, until callback
        self.sessions: dict[str, dict] = {}  # session id -> who is signed in
        self.db = store.connect()
        # Register with the identity provider, as an admin would in Okta or Entra ID.
        CLIENTS[CLIENT_ID] = {"secret": self.secret, "redirect_uris": [f"{self.base}/callback"]}

    def step(self, text: str) -> None:
        if self.verbose:
            print(f"  app  {text}", flush=True)


class AppHandler(BaseHTTPRequestHandler):
    server: App

    def do_GET(self) -> None:
        url = urllib.parse.urlsplit(self.path)
        session = self._session()
        if url.path == "/":
            self._redirect("/invoices" if session else "/login")
        elif url.path == "/login":
            self._login()
        elif url.path == "/callback":
            self._callback(dict(urllib.parse.parse_qsl(url.query)))
        elif url.path == "/logout":
            self.server.sessions.pop(self._cookie("session") or "", None)
            self._redirect("/", cookie="session=; Path=/; Max-Age=0")
        elif not session:
            self._send(401, "application/json", json.dumps({"error": "sign in first"}))
        elif url.path == "/invoices":
            self._invoices(session)
        elif match := re.fullmatch(r"/api/invoices/(\d+)", url.path):
            invoice = store.get_invoice(self.server.db, session["tenant"], int(match[1]))
            status = 200 if invoice else 404
            self._send(status, "application/json", json.dumps(invoice or {"error": "not_found"}))
        else:
            self._send(404, "application/json", json.dumps({"error": "not_found"}))

    def do_POST(self) -> None:
        session = self._session()
        match = re.fullmatch(r"/invoices/(\d+)/void", self.path)
        if not session or not match:
            self._send(404, "application/json", json.dumps({"error": "not_found"}))
            return
        if not can(session["roles"], "invoices:void"):
            self.server.step(f"403 {session['email']} may not void invoices")
            self._send(403, "text/html; charset=utf-8", page("Forbidden", FORBIDDEN))
            return
        store.void_invoice(self.server.db, session["tenant"], int(match[1]))
        self._redirect("/invoices")

    def _login(self) -> None:
        state, nonce = secrets.token_urlsafe(16), secrets.token_urlsafe(16)
        verifier = secrets.token_urlsafe(48)
        self.server.logins[state] = {"nonce": nonce, "verifier": verifier}
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": f"{self.server.base}/callback",
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": pkce_challenge(verifier),
                "code_challenge_method": "S256",
            }
        )
        self.server.step("1. redirect to the identity provider with state, nonce, PKCE challenge")
        self._redirect(f"{self.server.issuer}/authorize?{query}", cookie=login_cookie(state))

    def _callback(self, params: dict) -> None:
        state = params.get("state", "")
        login = self.server.logins.pop(state, None)
        # The state must be the one this browser started with, or someone else began this login.
        if not login or not secrets.compare_digest(state, self._cookie("login_state") or ""):
            self._fail("state does not match: this login was not started here")
            return
        self.server.step("2. back with a one-time code; state matches")
        form = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": params.get("code", ""),
                "redirect_uri": f"{self.server.base}/callback",
                "client_id": CLIENT_ID,
                "client_secret": self.server.secret,
                "code_verifier": login["verifier"],
            }
        ).encode()
        try:
            request = urllib.request.Request(f"{self.server.issuer}/token", data=form)
            with urllib.request.urlopen(request, timeout=5) as response:
                tokens = json.load(response)
            self.server.step("3. swapped the code and PKCE verifier for tokens, server to server")
            claims = verify(
                tokens["id_token"], KEY, self.server.issuer, CLIENT_ID, nonce=login["nonce"]
            )
        except (OSError, KeyError, TokenError) as error:
            self._fail(f"could not finish sign-in: {error}")
            return
        self.server.step(f"4. ID token verified: {claims['email']}, tenant {claims['tenant']}")

        session_id = secrets.token_urlsafe(24)
        self.server.sessions[session_id] = {
            "sub": claims["sub"],
            "email": claims["email"],
            "tenant": claims["tenant"],
            "roles": claims["roles"],
            "id_token": tokens["id_token"],
        }
        self._redirect("/invoices", cookie=session_cookie(session_id))

    def _invoices(self, session: dict) -> None:
        rows = store.list_invoices(self.server.db, session["tenant"])
        may_void = can(session["roles"], "invoices:void")
        body = "".join(
            f"<tr><td>{r['id']}</td><td>{html.escape(r['customer'])}</td>"
            f"<td>{r['amount_cents'] / 100:,.2f}</td><td>{r['status']}</td><td>"
            + (
                f'<form method=post action="/invoices/{r["id"]}/void"><button>Void</button></form>'
                if r["status"] == "open"
                else ""
            )
            + "</td></tr>"
            for r in rows
        )
        roles = ", ".join(session["roles"])
        content = (
            f"<h1>Invoices</h1><p>{html.escape(session['email'])}"
            f" <span class=tag>tenant {html.escape(session['tenant'])}</span>"
            f" <span class=tag>{html.escape(roles)}</span> · <a href=/logout>Sign out</a></p>"
            f"<p>{'You can void open invoices.' if may_void else 'You can read, not void.'}</p>"
            "<table><tr><th>#</th><th>Customer</th><th>Amount</th><th>Status</th><th></th></tr>"
            f"{body}</table><details><summary>Your ID token (paste it into"
            f" <code>python -m sso decode</code>)</summary><pre>{session['id_token']}</pre>"
            "</details>"
        )
        self._send(200, "text/html; charset=utf-8", page("Invoices", content))

    def _session(self) -> dict | None:
        return self.server.sessions.get(self._cookie("session") or "")

    def _cookie(self, name: str) -> str | None:
        morsel = SimpleCookie(self.headers.get("Cookie", "")).get(name)
        return morsel.value if morsel else None

    def _fail(self, reason: str) -> None:
        self.server.step(f"sign-in refused: {reason}")
        body = f"<h1>Sign-in failed</h1><p>{html.escape(reason)}</p><a href=/login>Try again</a>"
        self._send(400, "text/html; charset=utf-8", page("Sign-in failed", body))

    def _redirect(self, location: str, cookie: str | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _send(self, status: int, content_type: str, body: str) -> None:
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        pass  # request lines carry codes and state; the app prints its own steps instead


FORBIDDEN = "<h1>403</h1><p>Your role cannot void invoices.</p><a href=/invoices>Back</a>"


def login_cookie(state: str) -> str:
    return f"login_state={state}; Path=/callback; HttpOnly; SameSite=Lax; Max-Age=300"


def session_cookie(session_id: str) -> str:
    # HttpOnly: page scripts cannot read it. SameSite=Lax: other sites cannot POST with it.
    return f"session={session_id}; Path=/; HttpOnly; SameSite=Lax"
