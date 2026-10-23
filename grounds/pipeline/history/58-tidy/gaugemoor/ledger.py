"""The batch ledger: which drops have already been processed.

The ledger lives at var/ledger.json and is never edited by hand (D16): an
edited ledger makes the next batch reprocess or skip drops.
"""
import hashlib
import json
from pathlib import Path

DEFAULT_LEDGER = "var/ledger.json"


def drop_key(drop) -> str:
    """The key a drop is recorded under."""
    return hashlib.sha256(drop.data).hexdigest()


class Ledger:
    """A set of drop keys, saved as JSON."""

    def __init__(self, keys=()):
        self._keys: set[str] = set(keys)

    def __len__(self) -> int:
        return len(self._keys)

    def __contains__(self, key: str) -> bool:
        return key in self._keys

    def seen(self, drop) -> bool:
        """True if this drop was processed by an earlier run."""
        return drop_key(drop) in self._keys

    def add(self, drop) -> None:
        """Record a drop as processed."""
        self._keys.add(drop_key(drop))

    def to_json(self) -> str:
        return json.dumps({"version": 1, "keys": sorted(self._keys)}, indent=1)

    @classmethod
    def from_json(cls, text: str) -> "Ledger":
        data = json.loads(text)
        if data.get("version") != 1:
            raise ValueError(f"unknown ledger version: {data.get('version')!r}")
        return cls(data["keys"])


def read(path=DEFAULT_LEDGER) -> Ledger:
    """The ledger at `path`, or an empty one if there is none yet."""
    path = Path(path)
    if not path.exists():
        return Ledger()
    return Ledger.from_json(path.read_text(encoding="utf-8"))


def write(ledger: Ledger, path=DEFAULT_LEDGER) -> None:
    """Save the ledger, replacing the file in one step."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(ledger.to_json(), encoding="utf-8")
    tmp.replace(path)
