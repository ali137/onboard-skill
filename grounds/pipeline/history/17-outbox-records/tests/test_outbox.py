import io
import json
from datetime import datetime, timezone

from gaugemoor import outbox
from gaugemoor.alerts import Alert

UTC = timezone.utc
AT = datetime(2026, 10, 19, 14, 15, tzinfo=UTC)
WARNING = Alert("HB01", "warning", 2430, AT)


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
