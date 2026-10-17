# AGENTS.md

Guidance for AI coding agents and developers. Humans: start with [README.md](README.md).

## What this is

A short workshop, "Enterprise auth, hands on": an OIDC identity provider and an app on localhost,
roles, a deliberate cross-tenant leak to find, SAML checks and Postgres row-level security. The
lab in `lab/` and the chapters in `workshop/` are the product; `frontend/` is the site.

## Map

```text
lab/sso/idp.py          identity provider: USERS, CLIENTS, /authorize (PKCE S256), /token
lab/sso/app.py          the invoices app: /login, /callback, sessions, /invoices, /api/invoices/N
lab/sso/tokens.py       sign, decode, verify (HS256 only; alg, signature, iss, aud, exp, nonce)
lab/sso/rbac.py         PERMISSIONS and can()
lab/sso/store.py        SQLite invoices for two tenants; get_invoice ignores the tenant ON PURPOSE
lab/sso/saml.py         parse an assertion and list problems (no signature check, by design)
lab/sso/__main__.py     CLI: serve, decode, probe, saml
lab/postgres/rls.sql    chapter 07, run in a throwaway postgres:17 container
workshop/NN-slug.md     chapters; code quoted from lab/ must match it exactly
frontend/               Next.js site; reads ../workshop at build time
```

## Commands

```bash
cd lab && uv sync && uv run python -m sso probe
cd frontend && npm ci && npm run verify
```

## Rules

1. **No runtime dependencies** in `lab/`. Standard library only, so it runs anywhere.
2. **The leak in `store.get_invoice` is the chapter 06 exercise.** Do not fix it in the repo.
3. **Localhost only.** Servers bind to 127.0.0.1 and log no URLs, codes or tokens.
4. **Chapters quote real code and real output.** A unit test checks the code quoted in chapters
   02, 05 and 07 and every file path chapters mention.
5. **Writing style.** Plain English, short sentences, no em dashes. Conventional Commits, no AI
   attribution trailers.
