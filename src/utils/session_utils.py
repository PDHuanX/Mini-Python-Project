import json
import time
from pathlib import Path

SESSION_FILE = Path("resources/session.json")
SESSION_TTL_HOURS = 12

def save_session(session: dict) -> None:
    session["expire_at"] = time.time() + SESSION_TTL_HOURS * 3600
    SESSION_FILE.write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")


def load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        session = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if session.get("expire_at", 0) < time.time():
        clear_session()
        return None
    return session


def clear_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()