"""Persistência simples em arquivos (versionados pelo próprio GitHub)."""
import csv
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OBS = os.path.join(DATA, "observacoes.csv")
STATE = os.path.join(DATA, "estado.json")
LOG = os.path.join(DATA, "verificacoes.csv")

OBS_FIELDS = ["ts", "source", "id", "model", "bundle", "store", "price", "price_card",
              "status", "kind", "title", "url"]
LOG_FIELDS = ["ts", "source", "query", "ok", "items", "error"]
MAX_LOG_LINES = 5000


def _ensure():
    os.makedirs(DATA, exist_ok=True)


def load_obs(days: int | None = None) -> list[dict]:
    if not os.path.exists(OBS):
        return []
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = []
    with open(OBS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            r["price"] = float(r["price"]) if r["price"] else None
            r["price_card"] = float(r["price_card"]) if r.get("price_card") else None
            if cutoff and datetime.fromisoformat(r["ts"]) < cutoff:
                continue
            rows.append(r)
    return rows


def append_obs(rows: list[dict]):
    _ensure()
    new = not os.path.exists(OBS)
    with open(OBS, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OBS_FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def load_state() -> dict:
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"alerted": {}, "last_seen": {}, "fail_streak": 0, "health_alerted": False}


def save_state(state: dict):
    _ensure()
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def append_log(rows: list[dict]):
    _ensure()
    lines = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8", newline="") as f:
            lines = list(csv.DictReader(f))
    lines.extend(rows)
    lines = lines[-MAX_LOG_LINES:]
    with open(LOG, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(lines)
