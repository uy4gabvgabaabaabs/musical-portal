#!/usr/bin/env python3
"""Refresh stable downloadable CSVs from the portal's live source tables."""

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DOWNLOADS = PUBLIC / "downloads"


def rows(name: str):
    with (PUBLIC / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_complete():
    films = rows("musical_portal_4409.csv")
    extras = {
        name: {row["film_id"]: row for row in rows(name)}
        for name in ("film_genres.csv", "film_formats.csv", "film_styles.csv")
    }
    base_fields = list(films[0])
    insert_at = base_fields.index("collection")
    added = ["genre_1", "genre_2", "format", "style_1", "style_2"]
    fields = base_fields[:insert_at] + added + base_fields[insert_at:]
    with (DOWNLOADS / "musical_portal_complete.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for film in films:
            film_id = film["film_id"]
            enriched = dict(film)
            for name in extras:
                enriched.update({key: value for key, value in extras[name].get(film_id, {}).items() if key in added})
            writer.writerow(enriched)


def main():
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    build_complete()
    shutil.copyfile(PUBLIC / "animations.csv", DOWNLOADS / "animations_all.csv")
    shutil.copyfile(PUBLIC / "music_centered_films.csv", DOWNLOADS / "music_centered_films.csv")


if __name__ == "__main__":
    main()
