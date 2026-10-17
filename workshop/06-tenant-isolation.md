# Tenant isolation: find the leak

> Every query in a multi-tenant app needs the tenant in it. This app forgot once. Find the leak with a probe, fix it in one line, and prove it.

**Time:** 15 minutes

## Goal

Find a cross-tenant data leak the way an attacker would, fix it, and learn the habit that stops this whole class of bug.

## Run the probe

The probe signs in as Carol from globex, through the real SSO flow, then asks the JSON API for invoices 1 to 6 by id:

```bash
uv run python -m sso probe
```

```text
signed in as carol (tenant globex); asking for invoices 1 to 6 by id

  1  200  LEAK  acme    Wayne Industries
  2  200  LEAK  acme    Stark Logistics
  3  200  LEAK  acme    Oscorp
  4  200  ok    globex  Initech
  5  200  ok    globex  Hooli
  6  404

3 invoices from another tenant
```

Carol cannot see acme's invoices on her page. She can read every one of them through the API, just by counting. This is an IDOR (insecure direct object reference), and in a multi-tenant product it means one customer reading another customer's data: the worst incident a B2B company can have.

## Find it

The session knows Carol's tenant, and the page is correct. So the bug is in the path the API takes. Follow `/api/invoices/` in `lab/sso/app.py` to the function it calls in `lab/sso/store.py`, and compare it with `list_invoices` and `void_invoice` in the same file. One of the three ignores an argument it was given.

## Fix it

Make the query filter by tenant as well as id, with the tenant as a bound parameter. Then run the probe again:

```text
  1  404
  2  404
  3  404
  4  200  ok    globex  Initech
  5  200  ok    globex  Hooli
  6  404

isolated: no other tenant
```

Notice the answer is `404`, not `403`. Another tenant's invoice must look exactly like one that does not exist, or the API still tells an attacker which ids are real.

## The habit

- **The tenant comes from the session, never from the request.** Not from a URL, a header or a form field the user can edit.
- **Every data function takes the tenant.** `store.py` already did; the bug was one function accepting it and not using it. A linter or code review rule can look for exactly that.
- **Test every query with two tenants.** The probe is that test. Run it in CI.
- **Then make the database enforce it too**, so the next forgotten filter is not a leak. That is chapter 07.

## Check it works

- Before the fix, the probe reports 3 leaks and exits with 1.
- After the fix, it prints `isolated: no other tenant` and exits with 0.

## Exercise

Run the probe as Alice (`--as alice`) before and after your fix. Then add an `/api/invoices` endpoint that lists invoices, and extend the probe in `lab/sso/__main__.py` to check that every row it returns belongs to the signed-in tenant.

### More to try

- Sequential ids make the leak easy to find. Would random UUIDs fix it? Explain why they only hide it.
- Some products keep each tenant in its own schema or database. List one advantage and one cost compared with a `tenant_id` column.
