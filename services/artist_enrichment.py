"""Service functions to enrich scraped artist data with Spotify metadata and cache it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from integrations.spotify_client import SpotifyClient, SpotifyConfigurationError


def _default_record(artist_name: str) -> dict[str, Any]:
    return {
        "artist_name": artist_name,
        "spotify": {
            "track_name": None,
            "track_id": None,
            "embed_url": None,
            "available": False,
            "status": "track_unavailable",
        },
    }


def enrich_and_cache_artists(
    scraped_artists: Iterable[dict[str, Any]],
    cache_path: str | Path = "cache/artists_spotify.json",
    market: str = "US",
) -> list[dict[str, Any]]:
    """Enrich scraped artist records and persist normalized spotify metadata cache."""
    client = SpotifyClient()
    output: list[dict[str, Any]] = []

    for artist in scraped_artists:
        artist_name = artist.get("artist_name") or artist.get("name") or ""
        enriched = dict(artist)
        enriched.update(_default_record(artist_name))

        if not artist_name:
            output.append(enriched)
            continue

        try:
            candidates = client.search_artist(artist_name)
            artist_id = client.resolve_artist_id(artist_name, candidates)
            if not artist_id:
                output.append(enriched)
                continue

            track = client.fetch_top_track(artist_id=artist_id, market=market)
            if not track:
                output.append(enriched)
                continue

            enriched["spotify"] = {
                "track_name": track.name,
                "track_id": track.id,
                "embed_url": track.embed_url,
                "available": True,
                "status": "ok",
            }
        except SpotifyConfigurationError:
            enriched["spotify"]["status"] = "spotify_not_configured"
        except Exception:
            enriched["spotify"]["status"] = "spotify_lookup_failed"

        output.append(enriched)

    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output
