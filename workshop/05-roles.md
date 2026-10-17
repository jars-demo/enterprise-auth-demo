# Roles and permissions

> The identity provider tells you someone is an admin. Your app decides what an admin may do, in one place, checked on the server.

**Time:** 12 minutes

## Goal

Read the lab's role-based access control, see the server refuse Bob, and add a role of your own.

## Roles in, permissions out

Roles arrive in the ID token as the `roles` claim. Customers manage them in their own identity provider, by putting people in groups. Your app maps roles to permissions in `lab/sso/rbac.py`:

```python
PERMISSIONS: dict[str, set[str]] = {
    "viewer": {"invoices:read"},
    "admin": {"invoices:read", "invoices:void"},
}
```

Code never asks "is this person an admin?". It asks "may this person void invoices?", with `can(roles, "invoices:void")`. When a customer asks for a new role next quarter, you add one line here, and no `if role == "admin"` hunt through the codebase.

## Checked on the server, every time

Sign in as Bob. The page says "You can read, not void" and still shows the Void buttons. Press one: `403`. Hiding a button is for usability; the check that matters is in `do_POST` in `lab/sso/app.py`, on every request:

```python
        if not can(session["roles"], "invoices:void"):
```

Anyone can send a POST without your UI. If the server does not check, the permission does not exist.

## Two rules for enterprise roles

1. **Unknown roles grant nothing.** A typo in the customer's group name, or a role you never heard of, must mean no access, not a crash and not full access. `can` returns `False` for them.
2. **Roles are per tenant.** Alice is an admin of acme, not of your whole system. Every permission check sits next to a tenant check, which is chapter 06.

## Check it works

- As Bob, voiding an invoice answers `403` and the terminal shows "may not void invoices".
- As Alice, the invoice changes to `void`.

## Exercise

Add a `billing` role that can read and void invoices but, later, nothing else. Give it to Bob by editing `USERS` in `lab/sso/idp.py`, restart `serve`, sign in as Bob, and void an invoice. Then hide the Void buttons for people who cannot use them, in `_invoices`.

### More to try

- Roles are copied into the session at sign-in, in `_callback`. If a customer removes Alice from the admin group at noon, when does this app find out? Write down two ways to make it sooner.
- Look up SCIM: how identity providers push user and group changes to apps, so access is removed without waiting for the next sign-in.
