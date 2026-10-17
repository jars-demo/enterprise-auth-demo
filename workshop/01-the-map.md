# The map

> SSO, OAuth 2.0, OIDC, SAML, roles, tenants, RLS: what each word means, which problem it solves, and a running app that uses them all.

**Time:** 10 minutes

## Goal

Run a real single sign-on flow on your laptop, sign in as three different people, and place every enterprise auth word on one map.

## Set up

You need [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you. The lab uses the Python standard library only.

```bash
git clone https://github.com/jars-demo/enterprise-auth-demo.git
cd enterprise-auth-demo/lab
uv sync
uv run python -m sso serve
```

```text
identity provider  http://127.0.0.1:8400
app                http://127.0.0.1:8401   <- open this
```

Two servers start. `lab/sso/idp.py` is an identity provider, the "Sign in with your company" side: Okta, Entra ID or Google Workspace in real life. `lab/sso/app.py` is your product, an invoices app that trusts that provider.

## Sign in three times

Open http://127.0.0.1:8401. You are sent to the identity provider, you pick a person, and you land back in the app:

| Person | Company (tenant) | Role   |
| ------ | ---------------- | ------ |
| Alice  | acme             | admin  |
| Bob    | acme             | viewer |
| Carol  | globex           | admin  |

Sign in as each one (use "Sign out" in between). Alice and Bob see the same three invoices, but only Alice can void them. Carol sees two different invoices. Watch the terminal: the app prints each step of the flow.

## The map

| Word                         | Answers                                       | In this lab           |
| ---------------------------- | --------------------------------------------- | --------------------- |
| **Authentication**           | who are you?                                  | the identity provider |
| **Authorization**            | what may you do?                              | your app              |
| **SSO**                      | one company login for many apps               | "Sign in with SSO"    |
| **OAuth 2.0**                | how an app gets a token without your password | the code flow, ch. 02 |
| **OpenID Connect (OIDC)**    | OAuth 2.0 plus a signed "who this is" token   | the ID token, ch. 03  |
| **SAML 2.0**                 | the older XML way to do SSO, still everywhere | ch. 04                |
| **Roles (RBAC)**             | groups of permissions                         | viewer, admin, ch. 05 |
| **Tenant**                   | one customer company and its data             | acme, globex, ch. 06  |
| **Row-level security (RLS)** | the database enforcing tenant boundaries      | Postgres, ch. 07      |

The one idea to keep: the identity provider says **who** someone is and which company and roles they have. Everything about **what they may touch** is your app's job, and that is where most real breaches happen.

## Check it works

- You signed in as Alice, Bob and Carol and saw two different sets of invoices.
- The terminal shows steps 1 to 4 for each sign-in.

## Exercise

Sign in as Bob and press "Void". What happens, and which file decided it? Then find where the app learns Bob's tenant and roles. Hint: it is not a database lookup.

### More to try

- Open http://127.0.0.1:8400/.well-known/openid-configuration. This discovery document is how real apps learn a provider's endpoints from one URL.
- Your company probably uses SSO for some tools. Note which provider it is, and whether the tools use OIDC or SAML.
