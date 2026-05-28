"""
SQLite cache layer for DuangDee horoscope app.
Pre-generate strategy: daily content generated at 5 AM via cron.
Permanent content generated once and stored forever.

Cache tiers:
  - daily: zodiac (12), chinese zodiac (12), tarot (22) — refreshed every midnight
  - permanent: birthday (7), siamsi (28), yam (8) — generated once
  - realtime: phone, compatibility — no cache (always unique input)
"""
import sqlite3, hashlib, json, os
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.db")

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'daily'
        );
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            feature TEXT NOT NULL,
            count INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_cache_type ON cache(type);
        CREATE INDEX IF NOT EXISTS idx_cache_created ON cache(created);
        CREATE INDEX IF NOT EXISTS idx_stats_date ON stats(date);
        CREATE INDEX IF NOT EXISTS idx_stats_feature ON stats(feature);
    """)
    db.commit()
    db.close()

def make_key(feature, *parts):
    """Create a deterministic cache key: feature:part1:part2:..."""
    raw = f"{feature}:" + ":".join(str(p) for p in parts)
    return raw

def get(feature, *parts):
    """Get cached value. Returns (value, created) or (None, None)."""
    key = make_key(feature, *parts)
    db = get_db()
    row = db.execute("SELECT value, created FROM cache WHERE key=?", (key,)).fetchone()
    db.close()
    if row:
        return row["value"], row["created"]
    return None, None

def set(feature, value, *parts, type="daily"):
    """Set cache value."""
    key = make_key(feature, *parts)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO cache (key, value, created, type) VALUES (?, ?, ?, ?)",
        (key, value, str(date.today()), type)
    )
    db.commit()
    db.close()

def get_daily(feature, *parts):
    """Get cache valid for today only."""
    key = make_key(feature, *parts)
    db = get_db()
    row = db.execute(
        "SELECT value, created FROM cache WHERE key=? AND created=?",
        (key, str(date.today()))
    ).fetchone()
    db.close()
    if row:
        return row["value"], row["created"]
    return None, None

def is_stale(feature):
    """Check if daily cache for a feature is stale (needs regeneration)."""
    today = str(date.today())
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) as cnt FROM cache WHERE type='daily' AND created=? AND key LIKE ?",
        (today, f"{feature}:%")
    ).fetchone()["cnt"]
    db.close()
    return count == 0

def track_stats(feature):
    """Record a usage stat for analytics."""
    today = str(date.today())
    db = get_db()
    db.execute(
        "INSERT INTO stats (date, feature, count) VALUES (?, ?, 1) "
        "ON CONFLICT DO NOTHING",
        (today, feature)
    )
    db.commit()
    db.close()

def get_all_daily(feature):
    """Get all today's cached entries for a feature. Returns list of (key, value)."""
    today = str(date.today())
    db = get_db()
    rows = db.execute(
        "SELECT key, value FROM cache WHERE type='daily' AND created=? AND key LIKE ?",
        (today, f"{feature}:%")
    ).fetchall()
    db.close()
    return [(r["key"], r["value"]) for r in rows]

def get_stats(days=7):
    """Get usage stats for last N days."""
    db = get_db()
    rows = db.execute(
        "SELECT date, feature, COUNT(*) as total FROM stats "
        "WHERE date >= date('now', ?) GROUP BY date, feature ORDER BY date DESC, feature",
        (f"-{days} days",)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def cache_size():
    """Return (row_count, db_size_bytes)."""
    db = get_db()
    count = db.execute("SELECT COUNT(*) as cnt FROM cache").fetchone()["cnt"]
    db.close()
    size = os.path.getsize(DB_PATH)
    return count, size


# === Content builders ===

ZODIAC_SIGNS = ["เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์", "ตุลย์", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"]
CHINESE_YEARS = ["ชวด", "ฉลู", "ขาล", "เถาะ", "มะโรง", "มะเส็ง", "มะเมีย", "มะแม", "วอก", "ระกา", "จอ", "กุน"]
BIRTHDAY_DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

MAJOR_ARCANA = [
    {"name": "The Fool", "th": "นักเดินทาง", "key": "fool"},
    {"name": "The Magician", "th": "นักมายากล", "key": "magician"},
    {"name": "The High Priestess", "th": "นักบวชหญิง", "key": "high_priestess"},
    {"name": "The Empress", "th": "จักรพรรดินี", "key": "empress"},
    {"name": "The Emperor", "th": "จักรพรรดิ", "key": "emperor"},
    {"name": "The Hierophant", "th": "นักปราชญ์", "key": "hierophant"},
    {"name": "The Lovers", "th": "คู่รัก", "key": "lovers"},
    {"name": "The Chariot", "th": "ราชรถ", "key": "chariot"},
    {"name": "Strength", "th": "พละกำลัง", "key": "strength"},
    {"name": "The Hermit", "th": "ฤาษี", "key": "hermit"},
    {"name": "Wheel of Fortune", "th": "วงล้อโชคชะตา", "key": "wheel"},
    {"name": "Justice", "th": "ความยุติธรรม", "key": "justice"},
    {"name": "The Hanged Man", "th": "ผู้ถูกแขวน", "key": "hanged"},
    {"name": "Death", "th": "การเปลี่ยนแปลง", "key": "death"},
    {"name": "Temperance", "th": "ความพอดี", "key": "temperance"},
    {"name": "The Devil", "th": "ปีศาจ", "key": "devil"},
    {"name": "The Tower", "th": "หอคอย", "key": "tower"},
    {"name": "The Star", "th": "ดวงดาว", "key": "star"},
    {"name": "The Moon", "th": "พระจันทร์", "key": "moon"},
    {"name": "The Sun", "th": "พระอาทิตย์", "key": "sun"},
    {"name": "Judgement", "th": "การพิพากษา", "key": "judgement"},
    {"name": "The World", "th": "โลก", "key": "world"},
]
