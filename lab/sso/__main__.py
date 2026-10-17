"""python -m sso serve | decode | probe | saml"""

import argparse
import contextlib
import http.cookiejar
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import saml
from .app import App
from .idp import IdentityProvider
from .tokens import TokenError, decode


def start(idp_port: int, app_port: int, verbose: bool = True) -> tuple[IdentityProvider, App]:
    idp = IdentityProvider(idp_port)
    app = App(app_port, idp.issuer, verbose)
    for server in (idp, app):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return idp, app


def sign_in(app: App, user: str) -> urllib.request.OpenerDirector:
    """Click through the whole SSO flow like a browser would, as `user`."""
    browser = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    with browser.open(f"{app.base}/login") as login_page:
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(login_page.url).query))
    form = urllib.parse.urlencode({**params, "user": user}).encode()
    with browser.open(f"{app.issuer}/authorize", data=form) as landed:
        assert urllib.parse.urlsplit(landed.url).path == "/invoices", landed.url
    return browser


def probe(user: str) -> int:
    _, app = start(0, 0, verbose=False)
    browser = sign_in(app, user)
    tenant = next(s for s in app.sessions.values())["tenant"]
    print(f"signed in as {user} (tenant {tenant}); asking for invoices 1 to 6 by id\n")
    leaks = 0
    for invoice_id in range(1, 7):
        try:
            with browser.open(f"{app.base}/api/invoices/{invoice_id}") as response:
                invoice = json.load(response)
        except urllib.error.HTTPError as error:
            print(f"  {invoice_id}  {error.code}")
            continue
        own = invoice["tenant_id"] == tenant
        leaks += not own
        mark = "ok  " if own else "LEAK"
        print(f"  {invoice_id}  200  {mark}  {invoice['tenant_id']:<7} {invoice['customer']}")
    print(f"\n{leaks} invoices from another tenant" if leaks else "\nisolated: no other tenant")
    return 1 if leaks else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sso")
    commands = parser.add_subparsers(dest="command", required=True)
    srv = commands.add_parser("serve", help="run the identity provider and the app")
    srv.add_argument("--idp-port", type=int, default=8400)
    srv.add_argument("--app-port", type=int, default=8401)
    dec = commands.add_parser("decode", help="show what is inside a JWT, without trusting it")
    dec.add_argument("token")
    prb = commands.add_parser("probe", help="sign in and ask for every invoice by id")
    prb.add_argument("--as", dest="user", default="carol", choices=["alice", "bob", "carol"])
    sml = commands.add_parser("saml", help="check a SAML assertion's conditions")
    sml.add_argument("file", type=Path)
    sml.add_argument("--now", help="check as of this time, e.g. 2026-03-02T09:01:00Z")
    args = parser.parse_args(argv)

    if args.command == "serve":
        idp, app = start(args.idp_port, args.app_port)
        print(f"identity provider  {idp.issuer}")
        print(f"app                {app.base}   <- open this\n")
        with contextlib.suppress(KeyboardInterrupt):
            threading.Event().wait()
        return 0

    if args.command == "decode":
        try:
            header, claims = decode(args.token)
        except TokenError as error:
            print(error)
            return 1
        print("header ", json.dumps(header))
        print("claims ", json.dumps(claims, indent=2))
        print("\nDecoded, not verified: anyone can make a token that decodes like this.")
        return 0

    if args.command == "probe":
        return probe(args.user)

    assertion = saml.parse(args.file.read_text(encoding="utf-8"))
    print(f"user        {assertion.name_id}")
    print(f"attributes  {assertion.attributes}")
    found = saml.problems(
        assertion,
        issuer="https://idp.acme.test",
        audience="https://invoices.example/saml/metadata",
        acs_url="https://invoices.example/saml/acs",
        now=saml.when(args.now) if args.now else None,
    )
    print()
    for problem in found:
        print(f"  reject: {problem}")
    if not found:
        print("  accept (the signature is not checked here, see saml.py)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
