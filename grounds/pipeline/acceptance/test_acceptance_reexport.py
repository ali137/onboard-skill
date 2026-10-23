"""Kept outside the ground; seed.py --check copies it into tests/ while it runs."""
from datetime import timedelta

from gaugemoor import batch
from gaugemoor.ingest import Drop
from gaugemoor.ledger import Ledger, drop_key
from test_batch import DAY, DELIVERED, EVENING, REGISTRY, SMOOTH, SPIKED, levels, velcor


def test_a_resend_is_taken_in_after_the_ledger_is_saved_and_read_back():
    name, store = "KW03_20261019.txt", {}
    led = Ledger()
    batch.run([Drop(name, velcor("KW03", DAY, SPIKED), DELIVERED)], led, store, REGISTRY)
    led = Ledger.from_json(led.to_json())
    report = batch.run([Drop(name, velcor("KW03", DAY, SMOOTH), DELIVERED + timedelta(hours=3))],
                       led, store, REGISTRY)
    assert report.processed == [name]
    assert levels(store, "KW03", EVENING) == [SMOOTH[85], SMOOTH[86]]


def test_a_one_byte_change_anywhere_changes_the_key():
    base = bytes(range(256)) * 8000
    key = drop_key(Drop("a.txt", base, DELIVERED))
    for off in (0, 1023, 1024, 5003, 70001, len(base) // 2 + 1, len(base) - 1500, len(base) - 1):
        changed = bytearray(base)
        changed[off] ^= 1
        assert drop_key(Drop("a.txt", bytes(changed), DELIVERED)) != key, off
