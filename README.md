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
