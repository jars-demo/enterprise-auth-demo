-- Row-level security: the database itself keeps tenants apart, even when app code forgets.
-- Run it (chapter 07):
--   docker run --rm -d --name rls -e POSTGRES_PASSWORD=workshop postgres:17
--   docker exec -i rls psql -U postgres -v ON_ERROR_STOP=0 < lab/postgres/rls.sql

DROP TABLE IF EXISTS invoices;
CREATE TABLE invoices (
    id           integer PRIMARY KEY,
    tenant_id    text    NOT NULL,
    customer     text    NOT NULL,
    amount_cents integer NOT NULL
);
INSERT INTO invoices VALUES
    (1, 'acme',   'Wayne Industries', 120000),
    (2, 'acme',   'Stark Logistics',   48500),
    (4, 'globex', 'Initech',           77000);

-- The app connects as this role. It is not the table owner and not a superuser, both of which
-- skip row-level security.
DROP ROLE IF EXISTS app_user;
CREATE ROLE app_user;
GRANT SELECT, INSERT, UPDATE ON invoices TO app_user;

ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

SET ROLE app_user;

\echo '--- as acme: two rows'
SET app.tenant_id = 'acme';
SELECT * FROM invoices;

\echo '--- as globex, asking for acme invoice 1 by id: no rows'
SET app.tenant_id = 'globex';
SELECT * FROM invoices WHERE id = 1;

\echo '--- as globex, writing a row for acme: refused by WITH CHECK'
INSERT INTO invoices VALUES (9, 'acme', 'Sneaky', 1);

\echo '--- no tenant set at all: no rows (fails closed)'
RESET app.tenant_id;
SELECT count(*) FROM invoices;

RESET ROLE;
