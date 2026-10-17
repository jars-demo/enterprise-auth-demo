"""Invoices for two companies in one database: the multi-tenant part."""

import sqlite3

INVOICES = [
    (1, "acme", "Wayne Industries", 120_000, "open"),
    (2, "acme", "Stark Logistics", 48_500, "open"),
    (3, "acme", "Oscorp", 9_900, "paid"),
    (4, "globex", "Initech", 77_000, "open"),
    (5, "globex", "Hooli", 310_000, "open"),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE invoices (id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL,"
        " customer TEXT NOT NULL, amount_cents INTEGER NOT NULL, status TEXT NOT NULL)"
    )
    conn.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?)", INVOICES)
    return conn


def list_invoices(conn: sqlite3.Connection, tenant: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM invoices WHERE tenant_id = ? ORDER BY id", (tenant,))
    return [dict(row) for row in rows]


def get_invoice(conn: sqlite3.Connection, tenant: str, invoice_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    return dict(row) if row else None


def void_invoice(conn: sqlite3.Connection, tenant: str, invoice_id: int) -> bool:
    changed = conn.execute(
        "UPDATE invoices SET status = 'void' WHERE id = ? AND tenant_id = ?",
        (invoice_id, tenant),
    ).rowcount
    conn.commit()
    return changed == 1
