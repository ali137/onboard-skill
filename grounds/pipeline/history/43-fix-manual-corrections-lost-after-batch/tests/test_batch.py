from datetime import date, datetime, timedelta, timezone

from gaugemoor import batch, stations
from gaugemoor.edits import Edit
from gaugemoor.ingest import Drop
from gaugemoor.ledger import Ledger

UTC = timezone.utc
REGISTRY = stations.load()
DAY = date(2026, 10, 19)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)

# A smooth day at Kestle Weir in mm (the file writes 152,0 cm rising to 190,0 cm).
SMOOTH = [1520 + 4 * i for i in range(96)]
# The same day as the logger first sent it: a false reading at 21:15 and 21:30.
SPIKED = [4180 if i in (85, 86) else tenths for i, tenths in enumerate(SMOOTH)]


def velcor(station, day, tenths, *, start=0, flag="OK", exported="20.10.2026 06:00", serial="VL2-40117"):
    """A Velcor VL-2 file: one row per slot from slot `start` on."""
    lines = ["# Velcor VL-2", f"# serial: {serial}", f"# station: {station}", f"# exported: {exported}"]
    midnight = datetime(day.year, day.month, day.day)
    for i, value in enumerate(tenths, start=start):
        t = midnight + i * SLOT
        lines.append(f"{station};{day:%d.%m.%Y};{t:%H:%M};{value // 10},{value % 10};12,6;{flag}")
    return ("\n".join(lines) + "\n").encode()


def amsel(station_id, day, levels):
    lines = ["station,timestamp,level_mm,flag"]
    for i, level in enumerate(levels):
        t = datetime(day.year, day.month, day.day) + i * SLOT
        lines.append(f"{station_id.lower()},{t:%Y-%m-%dT%H:%M:%S}Z,{level},OK")
    return ("\n".join(lines) + "\n").encode()


def at(day, hh, mm):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=UTC)


def levels(store, station_id, times):
    found = {r.ts: r.level_mm for r in store.values() if r.station == station_id}
    return [found[t] for t in times]


EVENING = [at(DAY, 21, 15), at(DAY, 21, 30)]


def test_one_day_file_fills_96_slots():
    store, ledger = {}, Ledger()
    report = batch.run([Drop("KW03_20261019.txt", velcor("KW03", DAY, SMOOTH), DELIVERED)], ledger, store, REGISTRY)
    assert report.processed == ["KW03_20261019.txt"]
    assert report.skipped == [] and report.problems == []
    assert len(store) == 96
    assert levels(store, "KW03", [at(DAY, 0, 0)]) == [1520]


def test_second_delivery_of_a_day_replaces_its_readings():
    name = "KW03_20261019.txt"
    store, ledger = {}, Ledger()
    batch.run([Drop(name, velcor("KW03", DAY, SPIKED), DELIVERED)], ledger, store, REGISTRY)
    assert levels(store, "KW03", EVENING) == [4180, 4180]

    # Velcor sends the day again with the evening rows put right.
    resent = Drop(name, velcor("KW03", DAY, SMOOTH), DELIVERED + timedelta(hours=3))
    report = batch.run([resent], ledger, store, REGISTRY)

    assert report.processed == [name]
    assert levels(store, "KW03", EVENING) == [SMOOTH[85], SMOOTH[86]]
    assert len(store) == 96


def test_the_same_file_delivered_again_is_skipped():
    name = "KW03_20261019.txt"
    data = velcor("KW03", DAY, SMOOTH)
    store, ledger = {}, Ledger()
    batch.run([Drop(name, data, DELIVERED)], ledger, store, REGISTRY)
    before = dict(store)

    report = batch.run([Drop(name, data, DELIVERED + timedelta(hours=5))], ledger, store, REGISTRY)

    assert report.skipped == [name]
    assert report.processed == []
    assert store == before


def test_a_new_days_file_is_processed():
    store, ledger = {}, Ledger()
    next_day = DAY + timedelta(days=1)
    batch.run([Drop("KW03_20261019.txt", velcor("KW03", DAY, SMOOTH), DELIVERED)], ledger, store, REGISTRY)
    report = batch.run(
        [Drop("KW03_20261020.txt", velcor("KW03", next_day, SMOOTH, exported="21.10.2026 06:00"), DELIVERED + timedelta(days=1))],
        ledger,
        store,
        REGISTRY,
    )
    assert report.processed == ["KW03_20261020.txt"]
    assert len(store) == 192


def test_two_stations_files_of_one_day_are_both_processed():
    store, ledger = {}, Ledger()
    drops = [
        Drop("KW03_20261019.txt", velcor("KW03", DAY, SMOOTH), DELIVERED),
        Drop("MF02_20261019.txt", velcor("MF02", DAY, SMOOTH, serial="VL2-40388"), DELIVERED),
    ]
    report = batch.run(drops, ledger, store, REGISTRY)
    assert report.processed == ["KW03_20261019.txt", "MF02_20261019.txt"]
    assert len(ledger) == 2


def test_manual_edit_survives_a_later_batch():
    slot = at(DAY, 21, 30)
    fix = Edit("KW03", slot, 1866, "false reading; level from the staff gauge", "wick")
    store, ledger = {}, Ledger()
    batch.run([Drop("KW03_20261019.txt", velcor("KW03", DAY, SPIKED), DELIVERED)], ledger, store, REGISTRY, edits=[fix])
    assert levels(store, "KW03", [slot]) == [1866]

    # A field visit downloads the evening again; the logger still holds the false reading.
    visit = Drop(
        "KW03_visit_20261020.txt",
        velcor("KW03", DAY, SPIKED[80:], start=80, flag="R", exported="20.10.2026 14:30"),
        DELIVERED + timedelta(hours=8),
    )
    report = batch.run([visit], ledger, store, REGISTRY, edits=[fix])

    assert report.processed == ["KW03_visit_20261020.txt"]
    assert levels(store, "KW03", [slot]) == [1866]
    assert levels(store, "KW03", [at(DAY, 21, 15)]) == [4180]


def test_later_drop_in_one_run_wins_a_shared_slot():
    store, ledger = {}, Ledger()
    first = Drop("HB01_a.csv", amsel("HB01", DAY, [1700, 1702]), DELIVERED)
    second = Drop("HB01_b.csv", amsel("HB01", DAY, [1701, 1703, 1706]), DELIVERED + timedelta(hours=1))
    batch.run([first, second], ledger, store, REGISTRY)
    assert levels(store, "HB01", [at(DAY, 0, 0), at(DAY, 0, 15), at(DAY, 0, 30)]) == [1701, 1703, 1706]


def test_unreadable_file_is_reported_and_left_for_the_next_run():
    store, ledger = {}, Ledger()
    odd = Drop("notes.txt", b"called the council about the weir\n", DELIVERED)
    report = batch.run([odd], ledger, store, REGISTRY)
    assert report.processed == []
    assert [p.drop for p in report.problems] == ["notes.txt"]
    assert not ledger.seen(odd)


def test_unknown_station_is_reported():
    store, ledger = {}, Ledger()
    report = batch.run([Drop("ZZ99.csv", amsel("ZZ99", DAY, [10]), DELIVERED)], ledger, store, REGISTRY)
    assert report.processed == []
    assert "ZZ99" in report.problems[0].text.upper()
    assert store == {}


def test_bad_lines_are_reported_and_the_rest_is_stored():
    store, ledger = {}, Ledger()
    data = amsel("TC04", DAY, [410, 412]) + b"tc04,2026-10-19T00:30:00Z,4l3,OK\n"
    report = batch.run([Drop("TC04.csv", data, DELIVERED)], ledger, store, REGISTRY)
    assert report.processed == ["TC04.csv"]
    assert len(report.problems) == 1
    assert len(store) == 2
