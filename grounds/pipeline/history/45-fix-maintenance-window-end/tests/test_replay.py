import io
import json
from datetime import datetime, timedelta, timezone

from gaugemoor import outbox, replay, stations
from gaugemoor.replay import Window
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


def test_replay_skips_maintenance_windows():
    # Orley Lock's logger was out of the water in its stilling well; the readings are not the river.
    levels = [2500, 2900, 3500, 3500, 2500]
    window = Window("OL05", START + SLOT, START + 4 * SLOT, "stilling well flushed")
    fh = io.StringIO()
    raised = replay.replay({"OL05": series("OL05", levels)}, REGISTRY, fh, maintenance=[window])
    assert raised == []


def test_window_for_another_station_does_not_apply():
    window = Window("HB01", START, START + timedelta(days=1))
    raised = replay.replay({"OL05": series("OL05", [2500, 2900])}, REGISTRY, io.StringIO(), maintenance=[window])
    assert [a.kind for a in raised] == ["warning"]


def test_maintenance_window_end_is_exclusive():
    window = Window("OL05", START, START + 2 * SLOT)
    levels = [3500, 3500, 2900]
    raised = replay.replay({"OL05": series("OL05", levels)}, REGISTRY, io.StringIO(), maintenance=[window])
    assert [(a.kind, a.at) for a in raised] == [("warning", START + 2 * SLOT)]


def test_window_covers_its_start():
    window = Window("OL05", START, START + SLOT)
    assert window.covers("OL05", START)
    assert not window.covers("OL05", START + SLOT)
    assert not window.covers("MF02", START)


def test_maintenance_file_loads():
    windows = replay.load_maintenance()
    assert windows
    assert all(w.start < w.end for w in windows)
    assert all(w.start.tzinfo is not None for w in windows)
    assert {w.station for w in windows} <= set(REGISTRY)
