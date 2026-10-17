# Row-level security, and the enterprise checklist

> Make Postgres refuse cross-tenant rows on its own, so a forgotten WHERE clause is a bug, not a breach. Then the list enterprise customers will ask you about.

**Time:** 15 minutes

## Goal

Turn on Postgres row-level security for a tenant column, watch it block the leak from chapter 06 at the database, and leave with a checklist for selling to enterprises.

## Policies, not promises

Chapter 06 fixed the leak in application code. Row-level security (RLS) adds a second wall: the database filters every query by a policy, whatever SQL the app sends. From `lab/postgres/rls.sql`:

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
```

`USING` filters what you can read, update and delete. `WITH CHECK` stops you writing rows for another tenant. The app tells Postgres who is asking, once per request, with `SET app.tenant_id = 'acme'`.

## Run it

You need Docker. Start Postgres, then run the script:

```bash
docker run --rm -d --name rls -e POSTGRES_PASSWORD=workshop postgres:17
docker exec -i rls psql -U postgres -v ON_ERROR_STOP=0 < postgres/rls.sql
```

Read the output section by section. As acme you see two rows. As globex, `SELECT * FROM invoices WHERE id = 1` returns nothing: the same query that leaked in chapter 06, harmless here. Writing an acme row as globex fails with "new row violates row-level security policy". With no tenant set, you see zero rows: it fails closed. Stop it with `docker stop rls`.

## Three traps

1. **Owners and superusers skip RLS.** The app must connect as a separate role, like `app_user` in the script. Use `FORCE ROW LEVEL SECURITY` if the owner must be filtered too.
2. **Connection pools reuse sessions.** Use `SET LOCAL app.tenant_id` inside a transaction, so the tenant cannot leak into the next request on the same connection.
3. **RLS is the second wall, not the first.** Keep the tenant filters in your queries. RLS catches what they miss.

## The enterprise checklist

What a security review from a large customer will ask, and where you met it today:

| They ask                                     | You answer with                                       |
| -------------------------------------------- | ----------------------------------------------------- |
| "Do you support SSO with our provider?"      | OIDC and SAML, chapters 02 to 04                      |
| "Can we manage access with our groups?"      | roles from the provider mapped to permissions, ch. 05 |
| "Is our data isolated from other customers?" | tenant scoping in code plus RLS, chapters 06 and 07   |
| "What happens when someone leaves?"          | short sessions, SCIM deprovisioning                   |
| "Can we enforce SSO for our domain?"         | verified domains, no password login for them          |
| "Can we see who did what?"                   | audit logs with user, tenant, action and time         |

## Check it works

- The script shows two rows for acme, none for globex asking for id 1, a policy error for the sneaky insert, and a count of 0 with no tenant.

## Exercise

Add an `audit_log` table to `lab/postgres/rls.sql` with `tenant_id`, `actor`, `action` and `at`, give it the same policy, and insert one row as acme and one as globex. Show that each tenant sees only its own history.

### More to try

- Change the app's `store.py` design on paper: where would `SET LOCAL app.tenant_id` go so that every request sets it exactly once?
- Pick one row of the checklist your product cannot answer yet, and write the smallest change that would let you answer it.
