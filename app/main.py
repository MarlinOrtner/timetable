from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import Artist
from .scraper import ScrapeError, load_cache, save_cache, scrape_sziget_lineup
from .spotify import SpotifyClient

app = FastAPI(title="Sziget Festival 2026 Lineup")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
spotify = SpotifyClient()


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/artists")


@app.get("/artists")
def list_artists(
    request: Request,
    genre: Optional[str] = Query(default=None),
    date: Optional[str] = Query(default=None),
    sort: str = Query(default="name", pattern="^(name|date)$"),
):
    all_artists = load_cache()
    artists = all_artists

    if genre:
        artists = [artist for artist in artists if genre.lower() in artist.genre.lower()]
    if date:
        artists = [artist for artist in artists if date.lower() in artist.performance_date.lower()]

    key = (lambda a: a.performance_date.lower()) if sort == "date" else (lambda a: a.name.lower())
    artists = sorted(artists, key=key)

    genres = sorted({artist.genre for artist in all_artists if artist.genre})
    dates = sorted({artist.performance_date for artist in all_artists if artist.performance_date})

    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "artists": artists,
            "filters": {"genre": genre or "", "date": date or "", "sort": sort},
            "all_genres": genres,
            "all_dates": dates,
        },
    )


@app.get("/artists/{slug}")
def artist_detail(request: Request, slug: str):
    artists = load_cache()
    artist = next((a for a in artists if a.slug == slug), None)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    if not artist.spotify_embed_url:
        track = spotify.top_track_for_artist(artist.name)
        if track:
            artist.spotify_track_name = track.name
            artist.spotify_track_artist = track.artist
            artist.spotify_embed_url = track.embed_url
            updated = [_merge_artist(item, artist) for item in artists]
            save_cache(updated)

    return templates.TemplateResponse("detail.html", {"request": request, "artist": artist})


@app.post("/scrape")
def run_scrape(limit: Optional[int] = None):
    try:
        artists = scrape_sziget_lineup(limit=limit)
    except ScrapeError as exc:
        cached = load_cache()
        return {
            "count": len(cached),
            "source": "cache",
            "error": str(exc),
        }

    save_cache(artists)
    return {"count": len(artists), "source": "live"}


def _merge_artist(existing: Artist, new: Artist) -> Artist:
    return new if existing.slug == new.slug else existing
