# Enterprise auth, hands on

A hands-on workshop on the auth that enterprise customers ask for: single sign-on with OAuth 2.0 and OpenID Connect (with PKCE), ID token verification, SAML, roles and permissions, multi-tenant data isolation, and Postgres row-level security.

**Workshop site:** [enterpriseauth.jishanahmed.in](https://enterpriseauth.jishanahmed.in)

## Quick start

You need [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you. The lab uses the Python standard library only. Docker is needed only for chapter 07.

```bash
git clone https://github.com/jars-demo/enterprise-auth-demo.git
cd enterprise-auth-demo/lab
uv sync
uv run python -m sso serve
```

Open http://127.0.0.1:8401 and sign in as Alice, Bob or Carol. The terminal prints each step of the flow.

## Commands

| Command                                           | What it does                                               |
| ------------------------------------------------- | ---------------------------------------------------------- |
| `uv run python -m sso serve`                      | the identity provider on `:8400` and the app on `:8401`    |
| `uv run python -m sso decode TOKEN`               | show what is inside a JWT, without trusting it             |
| `uv run python -m sso probe [--as carol]`         | sign in and ask for every invoice by id: finds the leak    |
| `uv run python -m sso saml samples/assertion.xml` | check a SAML assertion's issuer, audience, recipient, time |

## The workshop

| #   | Chapter                                                              | You learn                                    |
| --- | -------------------------------------------------------------------- | -------------------------------------------- |
| 01  | [The map](workshop/01-the-map.md)                                    | every word, one running app                  |
| 02  | [The OAuth 2.0 code flow, with PKCE](workshop/02-oauth-code-flow.md) | state, PKCE, exact redirects, one-time codes |
| 03  | [OIDC ID tokens](workshop/03-oidc-id-tokens.md)                      | decode is not verify; the five checks        |
| 04  | [SAML in one page](workshop/04-saml.md)                              | assertions, conditions, why not DIY          |
| 05  | [Roles and permissions](workshop/05-roles.md)                        | RBAC, checked on the server                  |
| 06  | [Tenant isolation: find the leak](workshop/06-tenant-isolation.md)   | a real cross-tenant leak, fixed and proven   |
| 07  | [Row-level security](workshop/07-row-level-security.md)              | Postgres RLS and the enterprise checklist    |

## Layout

```text
lab/sso/          identity provider, app, tokens, roles, store, SAML checks, CLI
lab/samples/      a SAML assertion to read
lab/postgres/     the row-level security script for chapter 07
workshop/         the chapters, in Markdown
frontend/         the workshop site (Next.js), which renders workshop/
```

The lab is for learning on `127.0.0.1`. It signs tokens with a shared HS256 key and does not verify SAML signatures, and it says so where it does. Use a maintained library and a real identity provider in production.

## Run the site locally

```bash
cd frontend
npm ci
npm run dev
```

## License

[MIT](LICENSE)
