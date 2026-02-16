"""Spotify integration utilities for artist -> top track enrichment."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, Optional

import requests

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyConfigurationError(RuntimeError):
    """Raised when Spotify credentials are missing or invalid."""


@dataclass
class SpotifyTrack:
    """Normalized Spotify track metadata for cached records."""

    id: str
    name: str

    @property
    def embed_url(self) -> str:
        return f"https://open.spotify.com/embed/track/{self.id}"


class SpotifyClient:
    """Thin API client using the Spotify Client Credentials flow."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.timeout = timeout
        self._token: Optional[str] = None

    def _basic_auth_header(self) -> str:
        if not self.client_id or not self.client_secret:
            raise SpotifyConfigurationError(
                "Missing Spotify credentials. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )

        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return base64.b64encode(credentials).decode("utf-8")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Retrieve and cache access token via client credentials flow."""
        if self._token and not force_refresh:
            return self._token

        response = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {self._basic_auth_header()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise SpotifyConfigurationError("Spotify token response did not include an access_token.")

        self._token = token
        return token

    def _get(self, path: str, **params: Any) -> Dict[str, Any]:
        token = self.get_access_token()
        response = requests.get(
            f"{SPOTIFY_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params={k: v for k, v in params.items() if v is not None},
            timeout=self.timeout,
        )

        if response.status_code == 401:
            token = self.get_access_token(force_refresh=True)
            response = requests.get(
                f"{SPOTIFY_API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params={k: v for k, v in params.items() if v is not None},
                timeout=self.timeout,
            )

        response.raise_for_status()
        return response.json()

    def search_artist(self, artist_name: str, limit: int = 5) -> list[dict[str, Any]]:
        payload = self._get("/search", q=artist_name, type="artist", limit=limit)
        return payload.get("artists", {}).get("items", [])

    def resolve_artist_id(self, scraped_artist_name: str, candidates: Iterable[Dict[str, Any]]) -> Optional[str]:
        """Resolve best artist match by name similarity plus popularity tie-break."""

        def normalized(text: str) -> str:
            return " ".join(text.lower().replace("&", "and").split())

        source = normalized(scraped_artist_name)
        best_item: Optional[Dict[str, Any]] = None
        best_score = 0.0

        for candidate in candidates:
            candidate_name = normalized(candidate.get("name", ""))
            if not candidate_name:
                continue

            name_score = SequenceMatcher(None, source, candidate_name).ratio()
            popularity_bonus = float(candidate.get("popularity", 0)) / 500.0
            score = name_score + popularity_bonus

            if candidate_name == source:
                score += 0.35

            if score > best_score:
                best_score = score
                best_item = candidate

        if not best_item:
            return None

        return best_item.get("id") if best_score >= 0.55 else None

    def fetch_top_track(self, artist_id: str, market: str = "US") -> Optional[SpotifyTrack]:
        """Fetch one top track with market-aware fallback."""
        market_candidates = [market, "GB", "DE", "JP", None]

        for market_candidate in market_candidates:
            payload = self._get(f"/artists/{artist_id}/top-tracks", market=market_candidate)
            tracks = payload.get("tracks", [])
            if not tracks:
                continue

            selected = tracks[0]
            track_id = selected.get("id")
            track_name = selected.get("name")
            if track_id and track_name:
                return SpotifyTrack(id=track_id, name=track_name)

        return None
