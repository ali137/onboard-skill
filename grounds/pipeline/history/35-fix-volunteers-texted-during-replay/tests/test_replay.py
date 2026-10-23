import io
import json
from datetime import datetime, timedelta, timezone

from gaugemoor import outbox, replay, stations
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
START = datetime(2026, 1, 17, 3, 0, tzinfo=UTC)
ARCHIVED = datetime(2026, 1, 18, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)


def series(station_id, levels, start=START):
    return [Reading(station_id, start + i * SLOT, level, "OK", ARCHIVED) for i, level in enumerate(levels)]


def records(fh):
    return [json.loads(line) for line in fh.getvalue().splitlines()]


def test_replay_raises_the_winter_alerts():
    fh = io.StringIO()
    raised = replay.replay({"HB01": series("HB01", [2200, 2350, 2420, 2600, 3020, 2700, 2100])}, REGISTRY, fh)
    assert [a.kind for a in raised] == ["warning", "severe", "warning", "cleared"]
    assert [r["kind"] for r in records(fh)] == ["warning", "severe", "warning", "cleared"]


def test_replay_writes_only_to_the_given_outbox(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("replay opened an outbox of its own")

    monkeypatch.setattr(outbox, "open_outbox", refuse)
    scratch = io.StringIO()
    raised = replay.replay({"TC04": series("TC04", [1100, 1220, 1250])}, REGISTRY, scratch)
    assert len(raised) == 1
    assert [r["station"] for r in records(scratch)] == ["TC04"]


def test_replay_runs_all_stations_in_one_time_order():
    fh = io.StringIO()
    readings = {
        "TC04": series("TC04", [1100, 1100, 1250]),
        "HB01": series("HB01", [2450], start=START + SLOT),
    }
    replay.replay(readings, REGISTRY, fh)
    assert [(r["station"], r["at"]) for r in records(fh)] == [
        ("HB01", "2026-01-17T03:15:00Z"),
        ("TC04", "2026-01-17T03:30:00Z"),
    ]


def test_dry_run_replay_writes_dry_run_records():
    fh = io.StringIO()
    replay.replay({"TC04": series("TC04", [1250, 1000])}, REGISTRY, fh, dry_run=True)
    assert [r["status"] for r in records(fh)] == ["dry-run", "dry-run"]


def test_replay_leaves_out_quarantined_readings():
    fh = io.StringIO()
    levels = [1500, 1510, 2200, 1515]  # 2200 is a false reading at Kestle Weir
    assert replay.replay({"KW03": series("KW03", levels)}, REGISTRY, fh) == []
    assert fh.getvalue() == ""
