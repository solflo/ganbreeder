import json
import sqlite3

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS image (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT UNIQUE NOT NULL,
    vector     TEXT NOT NULL,
    label      TEXT NOT NULL,
    parent1    INTEGER,
    parent2    INTEGER,
    stars      INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_parent1 ON image(parent1);
CREATE INDEX IF NOT EXISTS idx_stars ON image(stars);
"""


def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(_SCHEMA)


def insert_images(rows):
    keys = []
    with connect() as conn:
        for r in rows:
            conn.execute(
                "INSERT INTO image (key, vector, label, parent1, parent2)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    r["key"],
                    json.dumps(r["vector"]),
                    json.dumps(r["label"]),
                    r.get("parent1"),
                    r.get("parent2"),
                ),
            )
            keys.append(r["key"])
    return keys


def get_by_key(key):
    with connect() as conn:
        return conn.execute("SELECT * FROM image WHERE key = ?", (key,)).fetchone()


def key_of_id(image_id):
    with connect() as conn:
        row = conn.execute("SELECT key FROM image WHERE id = ?", (image_id,)).fetchone()
        return row["key"] if row else None


def children_keys(parent1):
    with connect() as conn:
        rows = conn.execute(
            "SELECT key FROM image WHERE parent1 = ? AND parent2 IS NULL ORDER BY id",
            (parent1,),
        ).fetchall()
        return [r["key"] for r in rows]


def add_star(key):
    with connect() as conn:
        conn.execute("UPDATE image SET stars = stars + 1 WHERE key = ?", (key,))


def latest(page, per_page=48):
    with connect() as conn:
        rows = conn.execute(
            "SELECT key, created_at FROM image WHERE stars > 0"
            " ORDER BY id DESC LIMIT ? OFFSET ?",
            (per_page, per_page * page),
        ).fetchall()
        return [dict(r) for r in rows]


def lineage(key):
    query = """
    WITH RECURSIVE parenttree AS (
        SELECT id, key, created_at, parent1 FROM image WHERE key = ?
        UNION ALL
        SELECT e.id, e.key, e.created_at, e.parent1
        FROM image e JOIN parenttree p ON p.parent1 = e.id
    )
    SELECT key, created_at FROM parenttree ORDER BY created_at DESC
    """
    with connect() as conn:
        rows = conn.execute(query, (key,)).fetchall()
        return [dict(r) for r in rows]


def homepage_keys(n=6):
    with connect() as conn:
        raw = conn.execute(
            "SELECT key FROM image WHERE parent1 IS NULL ORDER BY RANDOM() LIMIT ?",
            (n,),
        ).fetchall()
        starred = conn.execute(
            "SELECT key FROM image WHERE stars > 0 ORDER BY RANDOM() LIMIT ?",
            (n,),
        ).fetchall()
    return [r["key"] for r in raw] + [r["key"] for r in starred]


def count_images():
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM image").fetchone()["c"]
