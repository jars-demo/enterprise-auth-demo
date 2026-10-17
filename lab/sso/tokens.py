"""JSON Web Tokens, small enough to read: sign, decode and verify, HS256 only.

Real identity providers sign with RS256 or ES256 and publish their public keys (JWKS), so apps
never hold the signing key. HS256 keeps this lab in the standard library; every check below is
the same either way.
"""

import base64
import hashlib
import hmac
import json
import time


class TokenError(ValueError):
    pass


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(claims: dict, key: bytes) -> str:
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url(json.dumps(claims).encode())
    signature = hmac.new(key, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{b64url(signature)}"


def decode(token: str) -> tuple[dict, dict]:
    """Read the header and claims WITHOUT checking anything. For looking, never for trusting."""
    try:
        header, payload, _ = token.split(".")
        return json.loads(b64url_decode(header)), json.loads(b64url_decode(payload))
    except ValueError as error:
        raise TokenError("not a JWT") from error


def verify(
    token: str,
    key: bytes,
    issuer: str,
    audience: str,
    nonce: str | None = None,
    now: float | None = None,
) -> dict:
    header, claims = decode(token)
    if header.get("alg") != "HS256":
        raise TokenError(f"unexpected algorithm {header.get('alg')!r}")  # never accept "none"
    signed, _, signature = token.rpartition(".")
    expected = hmac.new(key, signed.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, b64url_decode(signature)):
        raise TokenError("bad signature")
    if claims.get("iss") != issuer:
        raise TokenError("wrong issuer")
    if claims.get("aud") != audience:
        raise TokenError("token was issued for another app")
    if claims.get("exp", 0) < (now if now is not None else time.time()):
        raise TokenError("token expired")
    if nonce is not None and claims.get("nonce") != nonce:
        raise TokenError("nonce does not match this login")
    return claims
