#!/usr/bin/env python3
"""Build the portal's standalone catalogue of all known documentaries."""

import csv
import re
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
WORKING = ROOT / "working_documentaries"
FILMS = PUBLIC / "musical_portal_4409.csv"
NEW_DOCUMENTARIES = WORKING / "documentaries_import_batch_v44.csv"
EXISTING_DOCUMENTARIES = WORKING / "documentaries_existing_portal_72.csv"
PORTAL_DOCUMENTARY_CANDIDATES = ROOT / "working_genres" / "documentary_candidates.csv"
EXCLUDED = PUBLIC / "documentaries_excluded_concert_tour.csv"
OUTPUT = PUBLIC / "documentaries.csv"
DOWNLOAD = PUBLIC / "downloads" / "documentaries_all.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_year(value: str) -> str:
    match = re.search(r"\d{4}", value or "")
    return match.group(0) if match else ""


def choose_portal_film(rows: list[dict[str, str]], title: str) -> dict[str, str]:
    if not rows:
        return {}
    normalized = title.casefold().replace(":", "").strip()
    exact = [row for row in rows if row.get("title", "").casefold().replace(":", "").strip() == normalized]
    candidates = exact or rows
    return max(candidates, key=lambda row: sum(bool(row.get(key)) for key in ("persian_title", "director", "country", "letterboxd_url", "wikipedia_url", "spotify_uri")))


def title_key(title: str, year: str) -> tuple[str, str]:
    normalized = re.sub(r"[^a-z0-9]+", "", (title or "").casefold())
    return normalized, clean_year(year)


def main() -> None:
    films = read_csv(FILMS)
    by_imdb: dict[str, list[dict[str, str]]] = {}
    by_title_year: dict[tuple[str, str], list[dict[str, str]]] = {}
    for film in films:
        if film.get("imdb_id"):
            by_imdb.setdefault(film["imdb_id"], []).append(film)
        by_title_year.setdefault(title_key(film.get("title", ""), film.get("year", "")), []).append(film)

    previous_rows = read_csv(OUTPUT) if OUTPUT.exists() else []
    previous_by_imdb = {row["imdb_id"]: row for row in previous_rows if row.get("imdb_id")}
    previous_ids = {
        row["imdb_id"]: row["documentary_id"]
        for row in previous_rows
        if row.get("imdb_id") and row.get("documentary_id")
    }
    next_id = max(
        [int(match.group(1)) for row in previous_rows if (match := re.search(r"(\d+)$", row.get("documentary_id", "")))]
        or [0]
    ) + 1

    excluded_imdb = {row.get("imdb_id", "") for row in read_csv(EXCLUDED)} if EXCLUDED.exists() else set()

    raw_source_rows = read_csv(EXISTING_DOCUMENTARIES) + read_csv(NEW_DOCUMENTARIES)
    source_by_imdb: dict[str, dict[str, str]] = {}
    for row in raw_source_rows:
        source_by_imdb.setdefault(row["imdb_id"], row)

    for candidate in read_csv(PORTAL_DOCUMENTARY_CANDIDATES):
        imdb_id = candidate.get("imdb_id", "")
        if not imdb_id or imdb_id in excluded_imdb or imdb_id in source_by_imdb:
            continue
        source_by_imdb[imdb_id] = {
            "title": candidate.get("title", ""),
            "year": candidate.get("year", ""),
            "imdb_id": imdb_id,
            "imdb_primary_title": candidate.get("title", ""),
            "imdb_year": candidate.get("year", ""),
            "imdb_type": "movie",
            "imdb_genres": candidate.get("imdb_genres", ""),
            "classification_basis": candidate.get("review_note") or "برچسب Documentary در IMDb",
            "import_decision": "ورود از فهرست موجود درگاه",
            "priority": "",
            "source_dataset": "فهرست مستندهای موجود درگاه",
        }

    source_rows = list(source_by_imdb.values())

    output_rows = []
    for source in sorted(source_rows, key=lambda row: (row.get("title", "").casefold(), clean_year(row.get("year", "")))):
        year = clean_year(source.get("imdb_year") or source.get("year", ""))
        title = source.get("imdb_primary_title") or source.get("title", "")
        candidates = (
            by_imdb.get(source.get("imdb_id", ""), [])
            or by_title_year.get(title_key(title, year), [])
            or by_title_year.get(title_key(source.get("title", ""), year), [])
        )
        film = choose_portal_film(candidates, title)
        imdb_id = source.get("imdb_id", "")
        previous = previous_by_imdb.get(imdb_id, {})
        documentary_id = previous_ids.get(imdb_id)
        if not documentary_id:
            documentary_id = f"MUS-D-{next_id:06d}"
            next_id += 1
        linked_film_ids = "; ".join(dict.fromkeys(row.get("film_id", "") for row in candidates if row.get("film_id")))
        genres = source.get("imdb_genres", "")
        is_music = any(item in {"Music", "Musical"} for item in re.split(r"[;,]", genres))
        source_dataset = source.get("source_dataset") or "برچسب موسیقی ۳۰نما"
        output_rows.append({
            "documentary_id": documentary_id,
            "film_id": film.get("film_id", ""),
            "linked_film_ids": linked_film_ids,
            "title": title,
            "persian_title": film.get("persian_title", ""),
            "year": year,
            "director": film.get("director", ""),
            "country": film.get("country", ""),
            "imdb_id": imdb_id,
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else "",
            "imdb_genres": source.get("imdb_genres", ""),
            "imdb_type": source.get("imdb_type", ""),
            "runtime_minutes": clean_year(source.get("runtime_minutes", "")) if len(source.get("runtime_minutes", "")) == 4 else (source.get("runtime_minutes", "").replace(".0", "")),
            "imdb_rating": source.get("imdb_rating", "").replace(".0", ""),
            "imdb_votes": source.get("imdb_votes", "").replace(".0", ""),
            "thirtynama_id": source.get("thirtynama_id", ""),
            "thirtynama_url": source.get("thirtynama_url", ""),
            "downloadroz_search_url": f"https://tracy.ingmar-bergman.com/search/?s={quote_plus(title)}",
            "letterboxd_url": film.get("letterboxd_url", ""),
            "wikipedia_url": film.get("wikipedia_url", ""),
            "spotify_uri": film.get("spotify_uri", ""),
            "source_status": "متصل به فیلم موجود" if film else "افزوده‌شده از برچسب موسیقی ۳۰نما",
            "source_dataset": source_dataset,
            "selection_basis": source.get("classification_basis", "ژانر Documentary همراه Music/Musical در IMDb"),
            "priority": source.get("priority", ""),
            "documentary_scope": "مستند موسیقایی" if is_music else "مستند عمومی",
            "duplicate_status": "چند رکورد فیلم با یک IMDb" if len(candidates) > 1 else "",
        })

    fields = list(output_rows[0])
    for path in (OUTPUT, DOWNLOAD):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(output_rows)

    assert len(output_rows) == len({row["imdb_id"] for row in output_rows})
    assert all(row["imdb_id"] and row["imdb_url"] for row in output_rows)
    print(
        f"documentaries={len(output_rows)} "
        f"linked={sum(bool(row['film_id']) for row in output_rows)} "
        f"music={sum(row['documentary_scope'] == 'مستند موسیقایی' for row in output_rows)} "
        f"general={sum(row['documentary_scope'] == 'مستند عمومی' for row in output_rows)}"
    )


if __name__ == "__main__":
    main()
