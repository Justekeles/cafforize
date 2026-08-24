import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_WATER = 1.5
DEFAULT_SPOONS = 2.0
DEFAULT_RATIO = DEFAULT_SPOONS / DEFAULT_WATER  # spoons per unit of water

_SCHEMA = """
CREATE TABLE IF NOT EXISTS brews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    water_amount REAL NOT NULL,
    spoons_used REAL NOT NULL,
    grade INTEGER,
    created_at TEXT NOT NULL,
    graded_at TEXT
);
"""

_db_path = None


def init_app(app):
    global _db_path
    _db_path = Path(app.config["DATABASE_PATH"])
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def _connect():
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now():
    return datetime.now(timezone.utc).isoformat()


def add_brew(water_amount: float, spoons_used: float) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO brews (water_amount, spoons_used, created_at) VALUES (?, ?, ?)",
            (water_amount, spoons_used, _now()),
        )
        return cur.lastrowid


def grade_brew(brew_id: int, grade: int) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE brews SET grade = ?, graded_at = ? WHERE id = ?",
            (grade, _now(), brew_id),
        )
        return cur.rowcount > 0


def delete_brew(brew_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM brews WHERE id = ?", (brew_id,))
        return cur.rowcount > 0


def get_history(limit: int = 25):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM brews ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_best_ratio():
    """Look at graded brews and find the ratio (spoons per unit water,
    rounded to 2 decimals) with the best average grade. Requires at least
    two graded brews at that ratio to count it as a real signal.
    Falls back to the historical default otherwise.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT water_amount, spoons_used, grade FROM brews WHERE grade IS NOT NULL"
        ).fetchall()

    buckets = {}
    for r in rows:
        if not r["water_amount"]:
            continue
        ratio = round(r["spoons_used"] / r["water_amount"], 2)
        buckets.setdefault(ratio, []).append(r["grade"])

    candidates = [
        (ratio, sum(grades) / len(grades), len(grades))
        for ratio, grades in buckets.items()
        if len(grades) >= 2
    ]

    if not candidates:
        return {
            "ratio": DEFAULT_RATIO,
            "source": "default",
            "avg_grade": None,
            "sample_size": 0,
        }

    candidates.sort(key=lambda c: (c[1], c[2]), reverse=True)
    ratio, avg_grade, count = candidates[0]
    return {
        "ratio": ratio,
        "source": "learned",
        "avg_grade": round(avg_grade, 2),
        "sample_size": count,
    }
