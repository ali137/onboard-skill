"""Stage-discharge rating curves: river flow from the level.

data/ratings.csv holds each rating as segments of the stage range,
    rating,from_mm,to_mm,a,b,h0_mm
and in a segment the flow is Q = a * (h - h0) ** b, with h - h0 in meters.
A segment covers from_mm < h <= to_mm. Below the cease-to-flow stage (h0 of the first
segment) the flow is zero. Flows are in m3/s.
"""
import csv
from dataclasses import dataclass
from pathlib import Path

from gaugemoor.stations import DATA_DIR

RATINGS_CSV = DATA_DIR / "ratings.csv"


@dataclass(frozen=True)
class Segment:
    from_mm: int
    to_mm: int
    a: float
    b: float
    h0_mm: int

    def covers(self, level_mm: int) -> bool:
        return self.from_mm < level_mm <= self.to_mm


@dataclass(frozen=True)
class Rating:
    name: str
    segments: tuple[Segment, ...]

    @property
    def cease_to_flow_mm(self) -> int:
        return self.segments[0].h0_mm

    @property
    def top_mm(self) -> int:
        """The top of the rated range; levels above it use the last segment."""
        return self.segments[-1].to_mm


def load(path=None) -> dict[str, Rating]:
    """Read ratings.csv: rating name -> Rating."""
    path = Path(path) if path is not None else RATINGS_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    grouped: dict[str, list[Segment]] = {}
    for row in rows:
        grouped.setdefault(row["rating"].strip(), []).append(
            Segment(
                from_mm=int(row["from_mm"]),
                to_mm=int(row["to_mm"]),
                a=float(row["a"]),
                b=float(row["b"]),
                h0_mm=int(row["h0_mm"]),
            )
        )
    ratings = {}
    for name, segments in grouped.items():
        segments.sort(key=lambda s: s.from_mm)
        ratings[name] = Rating(name, tuple(segments))
    return ratings


def segment_for(rating: Rating, level_mm: int) -> Segment | None:
    """The segment a level falls in; None below the rated range."""
    for seg in rating.segments:
        if seg.covers(level_mm):
            return seg
    if level_mm >= rating.top_mm:
        return rating.segments[-1]
    return None


def flow(rating: Rating, level_mm: int) -> float:
    """The flow in m3/s at `level_mm`; zero at or below the cease-to-flow stage."""
    if level_mm <= rating.cease_to_flow_mm:
        return 0.0
    seg = segment_for(rating, level_mm)
    if seg is None:
        return 0.0
    depth_m = (level_mm - seg.h0_mm) / 1000
    if depth_m <= 0:
        return 0.0
    q = seg.a * depth_m**seg.b
    return q
