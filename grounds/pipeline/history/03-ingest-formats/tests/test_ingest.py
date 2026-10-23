from datetime import datetime, timezone
from decimal import Decimal

import pytest

from gaugemoor import ingest
from gaugemoor.ingest import Drop, UnknownFormat

UTC = timezone.utc
RECEIVED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)

VELCOR = """\
# Velcor VL-2
# serial: VL2-40117
# station: KW03
# exported: 20.10.2026 06:00
KW03;19.10.2026;00:00;183,4;12,6;OK
KW03;19.10.2026;00:15;183,6;12,6;OK
KW03;19.10.2026;00:30;184,1;12,5;R
"""

AMSEL = """\
station,timestamp,level_mm,flag
hb01,2026-10-19T00:00:00Z,1712,OK
hb01,2026-10-19T00:15:00Z,1715,ok
"""


def drop(text, name="file.csv", encoding="utf-8"):
    return Drop(name, text.encode(encoding), RECEIVED)


def test_sniff_tells_the_formats_apart():
    assert ingest.sniff(VELCOR.encode()) == "velcor"
    assert ingest.sniff(AMSEL.encode()) == "amsel"


def test_unknown_file_is_refused():
    with pytest.raises(UnknownFormat):
        ingest.parse(drop("date,value\n2026-10-19,12\n"))


def test_velcor_rows_keep_local_time_and_centimeters():
    rows, problems = ingest.parse(drop(VELCOR))
    assert problems == []
    assert [r.value for r in rows] == [Decimal("183.4"), Decimal("183.6"), Decimal("184.1")]
    first = rows[0]
    assert first.station == "KW03"
    assert first.time == datetime(2026, 10, 19, 0, 0)
    assert first.time.tzinfo is None
    assert first.received == RECEIVED


def test_velcor_flags_are_kept():
    rows, _ = ingest.parse(drop(VELCOR))
    assert [r.flag for r in rows] == ["OK", "OK", "R"]


def test_amsel_rows_are_utc_and_keep_the_id_as_written():
    rows, problems = ingest.parse(drop(AMSEL))
    assert problems == []
    assert [r.station for r in rows] == ["hb01", "hb01"]
    assert rows[1].time == datetime(2026, 10, 19, 0, 15, tzinfo=UTC)
    assert rows[1].value == Decimal(1715)


def test_bad_lines_become_problems_and_the_rest_is_read():
    text = VELCOR + "KW03;19.10.2026;00:45;18x,0;12,5;OK\nKW03;19.10.2026;01:00;184,0\n"
    rows, problems = ingest.parse(drop(text, name="kw03.txt"))
    assert len(rows) == 3
    assert [(p.drop, p.line) for p in problems] == [("kw03.txt", 8), ("kw03.txt", 9)]
    assert "not a number" in problems[0].text
    assert "expected 6 fields" in problems[1].text


def test_amsel_timestamp_without_zone_is_a_problem():
    rows, problems = ingest.parse(drop(AMSEL + "hb01,2026-10-19T00:30:00,1716,OK\n"))
    assert len(rows) == 2
    assert "not in UTC" in problems[0].text


def test_blank_lines_are_ignored():
    rows, problems = ingest.parse(drop(VELCOR.replace("\n# exported", "\n\n# exported") + "\n\n"))
    assert len(rows) == 3
    assert problems == []


def test_latin_1_header_from_older_firmware():
    text = VELCOR.replace("# serial: VL2-40117", "# site: Kestle Weir, Grünhalde")
    rows, problems = ingest.parse(drop(text, encoding="latin-1"))
    assert len(rows) == 3
    assert problems == []


def test_byte_order_mark_does_not_hide_the_format():
    rows, _ = ingest.parse(drop(AMSEL, encoding="utf-8-sig"))
    assert len(rows) == 2


def test_row_for_another_station_is_a_problem():
    text = VELCOR + "MF02;19.10.2026;00:45;121,0;12,5;OK\n"
    rows, problems = ingest.parse(drop(text))
    assert len(rows) == 3
    assert problems[0].text == "row for MF02 in a file for KW03"


def test_velcor_header_fields():
    header = ingest.velcor_header(VELCOR)
    assert header["serial"] == "VL2-40117"
    assert header["exported"] == "20.10.2026 06:00"
