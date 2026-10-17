# OIDC ID tokens

> A JWT is three base64 strings anyone can read and anyone can write. What makes it trustworthy is the five checks you run before using it.

**Time:** 15 minutes

## Goal

Decode a real ID token, then read the verification code and prove that an edited token is refused.

## Look inside

Sign in, open "Your ID token" at the bottom of the invoices page, and copy it. Then:

```bash
uv run python -m sso decode PASTE_THE_TOKEN_HERE
```

You get the header (`"alg": "HS256"`) and the claims: `iss`, `sub`, `aud`, `exp`, `nonce`, plus `email`, `tenant` and `roles`. The command ends with a warning worth remembering: decoding is not verifying. The token is just base64; you can write one by hand that decodes to anything.

## The five checks

From `verify` in `lab/sso/tokens.py`:

```python
    if claims.get("iss") != issuer:
        raise TokenError("wrong issuer")
    if claims.get("aud") != audience:
        raise TokenError("token was issued for another app")
    if claims.get("exp", 0) < (now if now is not None else time.time()):
        raise TokenError("token expired")
    if nonce is not None and claims.get("nonce") != nonce:
        raise TokenError("nonce does not match this login")
```

Before those, the signature, with a constant-time comparison. And before even that, the algorithm: a token whose header says `"alg": "none"` must be refused, never treated as "no signature needed". That bug has shipped in real JWT libraries.

| Check     | Without it                                                |
| --------- | --------------------------------------------------------- |
| signature | anyone can write `"roles": ["admin"]`                     |
| `alg`     | `"alg": "none"` tokens skip the signature                 |
| `iss`     | a token from a different provider, or tenant, is accepted |
| `aud`     | a token issued to another app is replayed into yours      |
| `exp`     | a token leaked last month still works                     |
| `nonce`   | an old ID token is replayed into a new login              |

## ID token or access token?

The provider returned both. The **ID token** is for your app, about the user, and is used once at sign-in. The **access token** is for calling an API (`"aud": "invoices-api"`); APIs check it on every request. Never send an ID token to an API as a bearer token, and never read user identity from an access token you did not verify.

## Check it works

- `decode` shows your `tenant` and `roles` claims.
- You can say what each of the five checks protects against.

## Exercise

Write a short script, or use `uv run python`, that takes your ID token, decodes the claims with `decode` from `lab/sso/tokens.py`, changes `"roles"` to `["admin"]` while signed in as Bob, re-encodes the payload with `b64url`, and keeps the original signature. Pass it to `verify`. Which check refuses it? Then sign it with a key you made up. Which check refuses that?

### More to try

- Real providers sign with RS256 and publish public keys at a JWKS URL. Read your provider's `jwks_uri` and find the `kid` in a real token's header.
- Tokens are bigger than session cookies and cannot be revoked early. Look at how this app turns the ID token into a server-side session in `_callback`, and list one reason that is a good idea.
