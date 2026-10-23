import io
import json
from datetime import datetime, timezone

from gaugemoor import outbox
from gaugemoor.alerts import Alert

UTC = timezone.utc
AT = datetime(2026, 10, 19, 14, 15, tzinfo=UTC)
WARNING = Alert("HB01", "warning", 2430, AT)


class CountingFile:
    """Stands in for the outbox file and counts write calls."""

    def __init__(self):
        self.writes = []

    def write(self, text):
        self.writes.append(text)
        return len(text)


def test_record_has_the_gateway_fields_in_order():
    fh = io.StringIO()
    outbox.append(fh, WARNING)
    rec = json.loads(fh.getvalue())
    assert list(rec) == ["station", "kind", "level_mm", "at", "text", "status"]
    assert rec["station"] == "HB01"
    assert rec["kind"] == "warning"
    assert rec["level_mm"] == 2430
    assert rec["at"] == "2026-10-19T14:15:00Z"
    assert rec["status"] == "send"


def test_each_record_is_one_line():
    fh = io.StringIO()
    outbox.append(fh, WARNING)
    outbox.append(fh, Alert("HB01", "severe", 3010, AT))
    lines = fh.getvalue().split("\n")
    assert lines[-1] == ""
    assert [json.loads(line)["kind"] for line in lines[:-1]] == ["warning", "severe"]


def test_each_record_is_one_write():
    fh = CountingFile()
    outbox.append(fh, WARNING)
    outbox.append(fh, Alert("HB01", "severe", 3010, AT), dry_run=True)
    assert len(fh.writes) == 2
    assert all(w.endswith("\n") and w.count("\n") == 1 for w in fh.writes)
    assert json.loads(fh.writes[0])["kind"] == "warning"


def test_alert_text_fits_one_text_message():
    for station in outbox.SHORT_NAMES:
        for kind in ("warning", "severe", "cleared"):
            alert = Alert(station, kind, 12345, datetime(2026, 12, 31, 23, 45, tzinfo=UTC))
            assert len(outbox.text(alert)) <= outbox.MAX_TEXT


def test_text_names_the_station_level_and_time():
    message = outbox.text(Alert("OL05", "severe", 3420, AT))
    assert message.startswith("SEVERE FLOOD WARNING: Orley Lock (OL05) 3.42 m at 14:15 UTC 19 Oct.")
