"""The alert outbox: one JSON record per line, read by the Trust's SMS gateway.

The record format is the gateway's contract (D10); change it only through
Ysolde. A record that goes out to volunteers has status "send".
"""
import json

DEFAULT_OUTBOX = "var/outbox.jsonl"
SEND = "send"

NAMES = {
    "KW03": ("Kestle Weir", "Kestle Brook"),
    "HB01": ("Hollinby Bridge", "River Brindle"),
    "MF02": ("Marrow Ford", "River Brindle"),
    "TC04": ("Tansey Cut", "River Brindle"),
    "OL05": ("Orley Lock", "River Brindle"),
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
    """The message volunteers receive."""
    name, river = NAMES.get(alert.station, (alert.station, "river"))
    label = LABELS.get(alert.kind, alert.kind.upper())
    return (
        f"{SIGN_OFF} flood alerts. {label} for {name} on the {river}: the level was "
        f"{alert.level_mm / 1000:.2f} m at {alert.at:%H:%M} UTC on {alert.at.day} {alert.at:%B}. "
        f"Keep away from the banks and check brindlemoor-rivers.example for updates."
    )


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
    """Append one record to the open outbox `fh`."""
    rec = record(alert)
    line = json.dumps(rec, ensure_ascii=False)
    fh.write(line)
    fh.write("\n")
