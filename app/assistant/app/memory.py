"""Долговременная память о предпочтениях (SQLite, локально). Журнал действий НЕ ведётся (РЕШЕНО-6)."""
import os, sqlite3, time
from . import config

PATH = os.path.join(config.DATA, "memory.db")

def _db():
    c = sqlite3.connect(PATH)
    c.execute("CREATE TABLE IF NOT EXISTS prefs(key TEXT PRIMARY KEY, value TEXT, updated REAL)")
    return c

def remember(key, value):
    with _db() as c:
        c.execute("INSERT OR REPLACE INTO prefs VALUES(?,?,?)", (key.strip().lower(), value.strip(), time.time()))

def recall(key=""):
    with _db() as c:
        if key:
            r = c.execute("SELECT key,value FROM prefs WHERE key LIKE ?", (f"%{key.strip().lower()}%",)).fetchall()
        else:
            r = c.execute("SELECT key,value FROM prefs ORDER BY updated DESC LIMIT 30").fetchall()
    return r

def forget(key):
    with _db() as c:
        n = c.execute("DELETE FROM prefs WHERE key=?", (key.strip().lower(),)).rowcount
    return n
