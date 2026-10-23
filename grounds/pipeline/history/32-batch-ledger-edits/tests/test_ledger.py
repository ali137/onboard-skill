from datetime import datetime, timezone

from gaugemoor.ingest import Drop
from gaugemoor.ledger import Ledger, drop_key

UTC = timezone.utc
MONDAY = datetime(2026, 10, 19, 6, 5, tzinfo=UTC)
TUESDAY = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)

TEXT = b"station,timestamp,level_mm,flag\nhb01,2026-10-19T00:00:00Z,1712,OK\n"


def test_same_content_same_key():
    assert drop_key(Drop("a.csv", TEXT, MONDAY)) == drop_key(Drop("a.csv", TEXT, TUESDAY))


def test_different_content_different_key():
    other = TEXT.replace(b"1712", b"1713")
    assert drop_key(Drop("a.csv", TEXT, MONDAY)) != drop_key(Drop("a.csv", other, MONDAY))


def test_new_ledger_has_seen_nothing():
    ledger = Ledger()
    assert len(ledger) == 0
    assert not ledger.seen(Drop("a.csv", TEXT, MONDAY))


def test_added_drop_is_seen():
    ledger = Ledger()
    drop = Drop("a.csv", TEXT, MONDAY)
    ledger.add(drop)
    assert ledger.seen(drop)
    assert drop_key(drop) in ledger


def test_adding_the_same_drop_again_records_it_once():
    ledger = Ledger()
    ledger.add(Drop("a.csv", TEXT, MONDAY))
    ledger.add(Drop("a.csv", TEXT, TUESDAY))
    assert len(ledger) == 1


def test_json_round_trip():
    ledger = Ledger()
    ledger.add(Drop("a.csv", TEXT, MONDAY))
    ledger.add(Drop("b.csv", TEXT + b"hb01,2026-10-19T00:15:00Z,1715,OK\n", MONDAY))
    again = Ledger.from_json(ledger.to_json())
    assert len(again) == 2
    assert again.seen(Drop("a.csv", TEXT, TUESDAY))
