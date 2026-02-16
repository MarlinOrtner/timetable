from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

import requests

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"


@dataclass
class SpotifyTrack:
    name: str
    artist: str
    embed_url: str


class SpotifyClient:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None) -> None:
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")

    def _access_token(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            return None

        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {basic}"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=20)
        response.raise_for_status()
        token = response.json().get("access_token")
        return token

    def top_track_for_artist(self, artist_name: str) -> Optional[SpotifyTrack]:
        token = self._access_token()
        if not token:
            return None

        params = {
            "q": artist_name,
            "type": "track",
            "limit": 1,
            "market": "HU",
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(SPOTIFY_SEARCH_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()

        items = response.json().get("tracks", {}).get("items", [])
        if not items:
            return None

        track = items[0]
        track_name = track.get("name", "")
        artists = track.get("artists", [])
        primary_artist = artists[0].get("name", "") if artists else ""
        track_id = track.get("id", "")
        if not track_id:
            return None

        embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        return SpotifyTrack(name=track_name, artist=primary_artist, embed_url=embed_url)
