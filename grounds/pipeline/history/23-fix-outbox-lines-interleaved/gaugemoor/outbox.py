"""The alert outbox: one JSON record per line, read by the Trust's SMS gateway.

The record format is the gateway's contract (D10); change it only through
Ysolde. A record that goes out to volunteers has status "send" and a text that
fits one message.
"""
import json

DEFAULT_OUTBOX = "var/outbox.jsonl"
MAX_TEXT = 160  # one text message
SEND = "send"

SHORT_NAMES = {
    "KW03": "Kestle Weir",
    "HB01": "Hollinby Br",
    "MF02": "Marrow Ford",
    "TC04": "Tansey Cut",
    "OL05": "Orley Lock",
}
LABELS = {
    "warning": "FLOOD WARNING",
    "severe": "SEVERE FLOOD WARNING",
    "cleared": "Flood warning cleared",
}
SIGN_OFF = "Brindlemoor Rivers Trust"


def stamp(at) -> str:
    """An aware UTC datetime as the gateway expects it: 2026-10-19T14:15:00Z."""
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def text(alert) -> str:
    """The message volunteers receive, at most MAX_TEXT characters."""
    name = SHORT_NAMES.get(alert.station, alert.station)
    label = LABELS.get(alert.kind, alert.kind.upper())
    message = (
        f"{label}: {name} ({alert.station}) {alert.level_mm / 1000:.2f} m "
        f"at {alert.at:%H:%M} UTC {alert.at.day} {alert.at:%b}. {SIGN_OFF}"
    )
    return message[:MAX_TEXT]


def record(alert) -> dict:
    """The outbox record for `alert` (D10)."""
    rec = {
        "station": alert.station,
        "kind": alert.kind,
        "level_mm": alert.level_mm,
        "at": stamp(alert.at),
    }
    rec["text"] = text(alert)
    rec["status"] = SEND
    return rec


def append(fh, alert) -> None:
    """Append one record to the open outbox `fh` in a single write."""
    rec = record(alert)
    line = json.dumps(rec, ensure_ascii=False)
    fh.write(line + "\n")
