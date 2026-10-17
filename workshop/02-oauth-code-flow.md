# The OAuth 2.0 code flow, with PKCE

> Four steps, two redirects and one server-to-server call. Each parameter exists to stop one specific attack.

**Time:** 15 minutes

## Goal

Follow the authorization code flow step by step in the lab's code, and know why `state`, `nonce`, PKCE and exact redirect URIs are not optional.

## The four steps

Sign in once more and read the terminal:

```text
  app  1. redirect to the identity provider with state, nonce, PKCE challenge
  app  2. back with a one-time code; state matches
  app  3. swapped the code and PKCE verifier for tokens, server to server
  app  4. ID token verified: alice@acme.test, tenant acme
```

1. **Redirect out.** `_login` in `lab/sso/app.py` sends the browser to the provider's `/authorize` with `client_id`, `redirect_uri`, `scope`, and three random values.
2. **Redirect back.** After the user signs in, the provider sends the browser to `/callback?code=...&state=...`. The code is short-lived and works once.
3. **Exchange.** The app's server, not the browser, posts the code to `/token` and gets tokens back. Tokens never pass through the browser's address bar.
4. **Verify.** The app checks the ID token before trusting a word of it (chapter 03).

## Why each piece exists

| Piece                | Stops                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `state`              | login CSRF: an attacker finishing _their_ login in _your_ browser                             |
| PKCE                 | a stolen code being swapped for tokens: only the app that made the challenge has the verifier |
| exact `redirect_uri` | codes being sent to an attacker's URL                                                         |
| one-time, 60 s codes | replaying a code from a log or a browser history                                              |
| `nonce`              | replaying an old ID token into a new login                                                    |

PKCE in two lines: the app makes a random `verifier`, sends `SHA-256(verifier)` as the challenge in step 1, and sends the verifier itself in step 3. The provider checks they match. From `lab/sso/idp.py`:

```python
def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
```

## Break it on purpose

Copy the `/authorize` URL from your browser's address bar while the login page is open. Change the `redirect_uri` to `http://127.0.0.1:9999/callback` and load it. The provider refuses: the URI is not registered. That exact-match check, in `_check_request`, is what keeps codes from leaking to other sites.

## Check it works

- You can name the four steps without looking.
- The edited `redirect_uri` shows "redirect_uri is not registered for this client".

## Exercise

In `lab/sso/app.py`, find the line in `_callback` that sends the `code_verifier` and change it to send `"wrong"`. Restart `serve` and sign in. Which step fails, what does the provider answer, and what does the app show? Put it back.

### More to try

- Sign in, then press the browser's back button until you are on the `/callback?code=...` URL and reload it. Why does it fail the second time?
- Single-page apps and mobile apps cannot keep a `client_secret`. Read the `_token` method in `lab/sso/idp.py` and explain why PKCE is what keeps them safe.
