from services.artist_enrichment import enrich_and_cache_artists


class StubClient:
    def search_artist(self, artist_name, limit=5):
        return [{"id": "artist-1", "name": artist_name, "popularity": 50}]

    def resolve_artist_id(self, scraped_artist_name, candidates):
        return "artist-1"

    def fetch_top_track(self, artist_id, market="US"):
        class Track:
            id = "track-1"
            name = "Song A"
            embed_url = "https://open.spotify.com/embed/track/track-1"

        return Track()


def test_enrich_and_cache_artists(monkeypatch, tmp_path):
    monkeypatch.setattr("services.artist_enrichment.SpotifyClient", lambda: StubClient())
    out = enrich_and_cache_artists(
        [{"artist_name": "Daft Punk"}],
        cache_path=tmp_path / "artists.json",
    )
    assert out[0]["spotify"]["available"] is True
    assert out[0]["spotify"]["track_id"] == "track-1"


def test_unavailable_artist_keeps_graceful_state(monkeypatch, tmp_path):
    class MissingClient(StubClient):
        def resolve_artist_id(self, scraped_artist_name, candidates):
            return None

    monkeypatch.setattr("services.artist_enrichment.SpotifyClient", lambda: MissingClient())
    out = enrich_and_cache_artists(
        [{"artist_name": "Unknown Artist"}],
        cache_path=tmp_path / "artists.json",
    )
    assert out[0]["spotify"]["available"] is False
    assert out[0]["spotify"]["status"] == "track_unavailable"
