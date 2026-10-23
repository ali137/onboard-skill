from datetime import datetime, timedelta, timezone

from gaugemoor import batch, cli
from gaugemoor.stations import Reading

UTC = timezone.utc
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)


def test_bad_date_is_a_usage_error(capsys):
    assert cli.main(["bulletin", "19.10.2026"]) == 2
    assert "not a date" in capsys.readouterr().err


def test_help_lists_the_commands(capsys):
    assert cli.main(["--help"]) == 0
    out = capsys.readouterr().out
    for command in ("batch", "bulletin", "export", "replay"):
        assert command in out


def test_bulletin_command_prints_the_bulletin(monkeypatch, capsys):
    start = datetime(2026, 10, 19, tzinfo=UTC)
    store = {}
    for i in range(96):
        reading = Reading("HB01", start + i * timedelta(minutes=15), 1700 + 2 * i, "OK", DELIVERED)
        store[("HB01", reading.ts)] = reading
    monkeypatch.setattr(batch, "load_store", lambda path: store)

    assert cli.main(["bulletin", "2026-10-19"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Brindlemoor Rivers Trust - river levels for Monday 19 October 2026")
    assert "HB01  low 1.70 m  peak 1.89 m at 23:45" in out
