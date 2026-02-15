import os
from pathlib import Path

APP_NAME = "lowkey-backup"
DATA_DIR = Path(os.environ.get("LOWKEY_DATA_DIR", f"/var/lib/{APP_NAME}"))
LOG_DIR = Path(os.environ.get("LOWKEY_LOG_DIR", f"/var/log/{APP_NAME}"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("LOWKEY_DB_PATH", str(DATA_DIR / "lowkey-backup.sqlite3")))
