from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class Artist:
    name: str
    slug: str
    genre: str
    biography: str
    performance_date: str
    source_url: str
    spotify_track_name: str = ""
    spotify_track_artist: str = ""
    spotify_embed_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Artist":
        return cls(**payload)
