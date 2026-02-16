from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template, request

app = Flask(__name__)
DATA_PATH = Path(__file__).parent / "data" / "artists.json"


def load_artists() -> list[dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        artists = json.load(f)

    for artist in artists:
        artist["performance_date"] = datetime.strptime(artist["date"], "%Y-%m-%d")
    return artists


@app.route("/")
def artist_list() -> str:
    artists = load_artists()

    genre_filter = request.args.get("genre", "").strip()
    date_filter = request.args.get("date", "").strip()
    sort_by = request.args.get("sort", "date_asc")

    if genre_filter:
        artists = [a for a in artists if a["genre"].lower() == genre_filter.lower()]

    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            artists = [a for a in artists if a["performance_date"].date() == selected_date]
        except ValueError:
            date_filter = ""

    if sort_by == "date_desc":
        artists = sorted(artists, key=lambda a: a["performance_date"], reverse=True)
    elif sort_by == "name_asc":
        artists = sorted(artists, key=lambda a: a["name"].lower())
    elif sort_by == "name_desc":
        artists = sorted(artists, key=lambda a: a["name"].lower(), reverse=True)
    else:
        sort_by = "date_asc"
        artists = sorted(artists, key=lambda a: a["performance_date"])

    genres = sorted({artist["genre"] for artist in load_artists()})

    return render_template(
        "list.html",
        artists=artists,
        genres=genres,
        selected_genre=genre_filter,
        selected_date=date_filter,
        selected_sort=sort_by,
    )


@app.route("/artist/<artist_id>")
def artist_detail(artist_id: str) -> str:
    artists = load_artists()
    artist = next((a for a in artists if a["id"] == artist_id), None)

    if artist is None:
        abort(404)

    return render_template("detail.html", artist=artist)


if __name__ == "__main__":
    app.run(debug=True)
