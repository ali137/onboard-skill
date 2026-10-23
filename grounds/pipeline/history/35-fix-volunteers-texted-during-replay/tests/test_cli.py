import io
from datetime import datetime, timedelta, timezone

from gaugemoor import batch, cli, outbox, replay
from gaugemoor.stations import Reading

UTC = timezone.utc
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)


class Scratch(io.StringIO):
    """An in-memory outbox that stays readable after the command closes it."""

    def close(self):
        self.saved = self.getvalue()
        super().close()


def test_bad_date_is_a_usage_error(capsys):
    assert cli.main(["bulletin", "19.10.2026"]) == 2
    assert "not a date" in capsys.readouterr().err


def test_help_lists_the_commands(capsys):
    assert cli.main(["--help"]) == 0
    out = capsys.readouterr().out
    for command in ("batch", "bulletin", "export", "replay"):
        assert command in out


def test_replay_outbox_defaults_to_the_outbox_path():
    args = cli.build_parser().parse_args(["replay", "var/archive/2025-26"])
    assert args.outbox == outbox.DEFAULT_OUTBOX
    assert args.dry_run is False


def test_replay_prints_the_outbox_path_it_writes_to(monkeypatch, capsys):
    opened = []
    scratch = Scratch()

    def fake_open(path):
        opened.append(path)
        return scratch

    readings = [
        Reading("TC04", datetime(2026, 1, 17, 3, 0, tzinfo=UTC) + i * timedelta(minutes=15), level, "OK", DELIVERED)
        for i, level in enumerate([1100, 1250])
    ]
    monkeypatch.setattr(replay, "load_archive", lambda directory, stations: {"TC04": readings})
    monkeypatch.setattr(outbox, "open_outbox", fake_open)

    code = cli.main(["replay", "var/archive/2025-26", "--outbox", "/scratch/check.jsonl", "--dry-run"])

    assert code == 0
    assert opened == ["/scratch/check.jsonl"]
    out = capsys.readouterr().out
    assert "replay: writing to /scratch/check.jsonl" in out
    assert "replay: 1 warning" in out
    assert '"status": "dry-run"' in scratch.saved


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
