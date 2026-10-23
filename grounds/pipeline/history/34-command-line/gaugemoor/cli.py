"""Command line: python3 -m gaugemoor <command> ...

    batch     take new drops from var/drops into the store, send alerts
    bulletin  print the daily bulletin for a day
    export    write the council export for a day
    replay    run the alert rules over an archive of logger files
"""
import argparse
import sys
from datetime import date
from pathlib import Path

from gaugemoor import alerts, batch, bulletin, clean, dedupe, edits, export, ledger, outbox, ratings, replay
from gaugemoor import stations as registry


def _day(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a date (YYYY-MM-DD): {text!r}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m gaugemoor", description="Brindlemoor river-level pipeline")
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = commands.add_parser("batch", help="take new drops into the store and send alerts")
    p.add_argument("--drops", default=batch.DEFAULT_DROPS)
    p.add_argument("--ledger", default=ledger.DEFAULT_LEDGER)
    p.add_argument("--store", default=batch.DEFAULT_STORE)

    p = commands.add_parser("bulletin", help="print the daily bulletin")
    p.add_argument("day", type=_day)
    p.add_argument("--store", default=batch.DEFAULT_STORE)

    p = commands.add_parser("export", help="write the council export for a day")
    p.add_argument("day", type=_day)
    p.add_argument("--store", default=batch.DEFAULT_STORE)
    p.add_argument("--out", help="file to write (default: standard output)")

    replay.add_arguments(commands.add_parser("replay", help="run the alert rules over an archive"))
    return parser


def send_alerts(readings, stations, outbox_path=outbox.DEFAULT_OUTBOX) -> list:
    """Evaluate new readings and append their alerts to the outbox."""
    path = Path(outbox_path)
    state = alerts.AlertState()
    grouped: dict[str, list] = {}
    for reading in readings:
        grouped.setdefault(reading.station, []).append(reading)
    raised = []
    with outbox.open_outbox(path) as fh:
        for station_id in sorted(grouped):
            station = stations[station_id]
            for alert in alerts.evaluate(station, clean.screen(station, grouped[station_id]), state):
                outbox.append(fh, alert)
                raised.append(alert)
    return raised


def cmd_batch(args) -> int:
    stations = registry.load()
    book = ledger.read(args.ledger)
    store = batch.load_store(args.store)
    before = dict(store)
    report = batch.run(batch.read_drops(args.drops), book, store, stations, edits.load())
    batch.save_store(store, args.store)
    ledger.write(book, args.ledger)
    fresh = [r for key, r in store.items() if before.get(key) != r and r.flag != edits.MANUAL_FLAG]
    raised = send_alerts(fresh, stations)
    print(f"{report.summary()}, {len(raised)} alerts")
    for problem in report.problems:
        print(f"  {problem.drop}:{problem.line}: {problem.text}", file=sys.stderr)
    return 0


def cmd_bulletin(args) -> int:
    stations = registry.load()
    store = batch.load_store(args.store)
    quarantine: list = []
    lines = bulletin.build(args.day, dedupe.by_station(store), stations, quarantine)
    print(bulletin.render(lines), end="")
    if quarantine:
        counts = clean.reasons(quarantine)
        held = ", ".join(f"{counts[reason]} {reason}" for reason in sorted(counts))
        print(f"held back by screening: {held}", file=sys.stderr)
    for station in stations.values():
        for first, last in clean.flatlines(station, dedupe.for_station(store, station.id)):
            if first.ts.date() <= args.day <= last.ts.date():
                print(f"{station.id}: level unchanged from {first.ts:%H:%M} to {last.ts:%H:%M} UTC", file=sys.stderr)
    return 0


def cmd_export(args) -> int:
    data = export.to_bytes(
        export.council_csv(batch.load_store(args.store), registry.load(), ratings.load(), args.day)
    )
    if args.out:
        Path(args.out).write_bytes(data)
        rows = data.count(b"\n") - 1
        print(f"export: {rows} rows written to {args.out}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(data)
    return 0


COMMANDS = {"batch": cmd_batch, "bulletin": cmd_bulletin, "export": cmd_export, "replay": replay.run}


def main(argv=None) -> int:
    parser = build_parser()
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in COMMANDS:
        parser.print_help()
        return 0
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    return COMMANDS[args.command](args)
