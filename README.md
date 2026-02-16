# Artist Timetable Flask App

A mobile-first Flask app that lists artists and provides detail pages with schedule data and Spotify embeds.

## Features

- Artist list page with filters for genre and date.
- Sort options for date and name.
- Artist detail page with bio, scheduled date, and embedded Spotify player.
- Responsive UI optimized for narrow/mobile viewports.

## Project structure

- `app.py` – Flask app and routes.
- `data/artists.json` – backend data source wired into templates.
- `templates/` – Jinja templates (`base.html`, `list.html`, `detail.html`).
- `static/css/styles.css` – mobile-first responsive styling.
- `static/js/app.js` – optional JS placeholder.

## Run locally

1. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app with a single command:
   ```bash
   flask --app app run
   ```

Then open <http://127.0.0.1:5000>.
# Sziget Festival 2026 Lineup Webapp

Mobile-first Python webapp that:
- Scrapes artist data from the official Sziget lineup page.
- Caches artist metadata locally.
- Enriches each artist detail page with a Spotify top-track embed.

## Stack
- **Backend:** FastAPI
- **Frontend:** Jinja2 templates + CSS (mobile optimized)
- **Scraping:** Playwright (handles SPA/dynamic behavior)
- **Music lookup:** Spotify Web API

## Features
- Artist list with **genre/date filters** and **sorting by name/date**.
- Artist detail with:
  - Name
  - Genre
  - Biography
  - Performance date
  - Spotify embedded player
- Cache file at `data/artists_cache.json` to avoid scraping on every request.
- Graceful scraper fallback: if live scraping fails, `/scrape` returns cached data and an error description.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m playwright install-deps chromium
```

## Spotify credentials
Set environment variables before starting the app:

```bash
export SPOTIFY_CLIENT_ID="<your_client_id>"
export SPOTIFY_CLIENT_SECRET="<your_client_secret>"
```

## Run server
```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Trigger scraping
Populate cache from live lineup:

```bash
curl -X POST "http://127.0.0.1:8000/scrape"
```

Optional limit for quick refresh:

```bash
curl -X POST "http://127.0.0.1:8000/scrape?limit=20"
```

If scraping cannot reach Sziget (network/proxy issues), response includes `source: cache` and an `error` field.

## Project structure
- `app/main.py` – FastAPI routes, filtering/sorting logic, template rendering.
- `app/scraper.py` – Playwright scraping + cache read/write.
- `app/spotify.py` – Spotify client credentials flow + top track lookup.
- `app/templates/` – list/detail views.
- `app/static/styles.css` – mobile-first styling.

## Notes
- Sziget selectors may evolve; scraper includes fallback selectors, scrolling for lazy-loaded cards, and regex date fallback extraction.
- Spotify tracks are looked up lazily when an artist detail page is opened, then cached.
