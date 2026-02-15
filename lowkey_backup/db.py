import sqlite3
from pathlib import Path
from .config import DB_PATH

SCHEMA = """CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,

  src_host TEXT NOT NULL,
  src_port INTEGER NOT NULL,
  src_user TEXT NOT NULL,
  src_auth_type TEXT NOT NULL,
  src_key_path TEXT,
  src_password TEXT,
  src_path TEXT NOT NULL,

  dst_host TEXT NOT NULL,
  dst_port INTEGER NOT NULL,
  dst_user TEXT NOT NULL,
  dst_auth_type TEXT NOT NULL,
  dst_key_path TEXT,
  dst_password TEXT,
  dst_path TEXT NOT NULL,

  days TEXT NOT NULL,
  time_hhmm TEXT NOT NULL,
  keep TEXT NOT NULL,
  type TEXT NOT NULL,

  last_run TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  message TEXT,
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
