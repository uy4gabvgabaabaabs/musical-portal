#!/usr/bin/env python3
"""Build the standalone animation catalogue and its person relations."""

import argparse
import csv
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
MASTER = PUBLIC / "musical_portal_4409.csv"
CANDIDATES = ROOT / "working_genres" / "animation_candidates.csv"
THIRTYNAMA = ROOT / "working_30nama" / "30nama-music-classified.csv"
OUTPUT = PUBLIC / "animations.csv"
CREDITS = PUBLIC / "animation_credits.csv"
FORMATS = PUBLIC / "film_formats.csv"
SOURCE_URL = "https://developer.imdb.com/non-commercial-datasets/"

ROLE_LABELS = {
    "director": "کارگردان",
    "writer": "نویسنده",
    "composer": "آهنگ‌ساز",
    "actor": "بازیگر / صداپیشه",
    "actress": "بازیگر / صداپیشه",
    "producer": "تهیه‌کننده",
    "cinematographer": "فیلم‌بردار",
    "editor": "تدوینگر",
}
ANIMATION_TERMS = re.compile(r"\b(animat|character design|layout artist|storyboard)\w*\b", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean(value: str | None) -> str:
    return "" if not value or value == r"\N" else value.strip()


def rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def split_ids(value: str | None) -> list[str]:
    return [part for part in clean(value).split(",") if part]


def write_csv(path: Path, fieldnames: list[str], output_rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def best_film(items: list[dict[str, str]]) -> dict[str, str]:
    if not items:
        return {}
    fields = ("persian_title", "director", "country", "actors", "composer", "letterboxd_url", "wikipedia_url", "spotify_uri")
    return max(items, key=lambda row: sum(bool(row.get(field)) for field in fields))


def append_name(values: list[str], value: str) -> None:
    if value and value.casefold() not in {item.casefold() for item in values}:
        values.append(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/musical-portal-imdb"))
    args = parser.parse_args()
    dataset_paths = {name: args.cache_dir / name for name in ("title.basics.tsv.gz", "title.crew.tsv.gz", "title.principals.tsv.gz", "name.basics.tsv.gz")}
    missing = [str(path) for path in dataset_paths.values() if not path.exists()]
    if missing:
        raise SystemExit(f"IMDb cache missing: {', '.join(missing)}")

    master_rows = read_csv(MASTER)
    master_by_imdb: dict[str, list[dict[str, str]]] = defaultdict(list)
    for film in master_rows:
        if film.get("imdb_id"):
            master_by_imdb[film["imdb_id"]].append(film)

    # Preserve the first appearance of every current portal animation.
    sources: dict[str, dict[str, str]] = {}
    for row in read_csv(CANDIDATES):
        imdb_id = row.get("imdb_id", "")
        if imdb_id and imdb_id not in sources:
            sources[imdb_id] = {
                **row,
                "source_scope": "موجودی پیشین درگاه",
                "imdb_type": "short" if "Short" in row.get("imdb_genres", "").split(",") else "movie",
            }

    # The official IMDb genre is the authoritative broad sweep.  This catches
    # portal films whose older local path/collection never carried an animation
    # label, without reviewing thousands of titles by hand.
    master_ids = set(master_by_imdb)
    for row in rows(dataset_paths["title.basics.tsv.gz"]):
        imdb_id = row["tconst"]
        if imdb_id not in master_ids or "Animation" not in split_ids(row.get("genres")):
            continue
        film = best_film(master_by_imdb[imdb_id])
        if imdb_id in sources:
            sources[imdb_id].update({
                "imdb_genres": clean(row.get("genres")),
                "imdb_type": clean(row.get("titleType")) or sources[imdb_id].get("imdb_type", "movie"),
            })
            continue
        sources[imdb_id] = {
            "film_id": film.get("film_id", ""),
            "imdb_id": imdb_id,
            "title": film.get("title", "") or clean(row.get("primaryTitle")),
            "persian_title": film.get("persian_title", ""),
            "year": film.get("year", "") or clean(row.get("startYear")),
            "director": film.get("director", ""),
            "country": film.get("country", ""),
            "imdb_genres": clean(row.get("genres")),
            "imdb_type": clean(row.get("titleType")) or "movie",
            "source_scope": "موجودی پیشین درگاه",
        }

    # Only feature-length/movie records are imported from 30nama.
    for row in read_csv(THIRTYNAMA):
        if row.get("music_category") != "انیمیشن" or row.get("imdb_type") != "movie":
            continue
        imdb_id = row.get("imdb_id", "")
        if not imdb_id:
            continue
        if imdb_id in sources:
            sources[imdb_id].update({
                "thirtynama_id": row.get("thirtynama_id", ""),
                "thirtynama_url": row.get("thirtynama_url", ""),
                "runtime_minutes": row.get("runtime_minutes", "").replace(".0", ""),
                "imdb_rating": row.get("imdb_rating", "").replace(".0", ""),
                "imdb_votes": row.get("imdb_votes", "").replace(".0", ""),
            })
        else:
            sources[imdb_id] = {
                "film_id": "",
                "imdb_id": imdb_id,
                "title": row.get("imdb_primary_title") or row.get("title", ""),
                "persian_title": "",
                "year": (row.get("imdb_year") or row.get("year", "")).replace(".0", ""),
                "director": "",
                "country": "",
                "imdb_genres": row.get("imdb_genres", "").replace(";", ","),
                "imdb_type": "movie",
                "source_scope": "افزوده از انیمیشن بلند ۳۰نما",
                "thirtynama_id": row.get("thirtynama_id", ""),
                "thirtynama_url": row.get("thirtynama_url", ""),
                "runtime_minutes": row.get("runtime_minutes", "").replace(".0", ""),
                "imdb_rating": row.get("imdb_rating", "").replace(".0", ""),
                "imdb_votes": row.get("imdb_votes", "").replace(".0", ""),
            }

    target_ids = set(sources)
    previous = read_csv(OUTPUT) if OUTPUT.exists() else []
    previous_ids = {row["imdb_id"]: row["animation_id"] for row in previous if row.get("imdb_id") and row.get("animation_id")}
    next_id = max([int(match.group(1)) for row in previous if (match := re.search(r"(\d+)$", row.get("animation_id", "")))] or [0]) + 1

    crew_directors: dict[str, list[str]] = {}
    crew_writers: dict[str, list[str]] = {}
    for row in rows(dataset_paths["title.crew.tsv.gz"]):
        if row["tconst"] in target_ids:
            crew_directors[row["tconst"]] = split_ids(row.get("directors"))
            crew_writers[row["tconst"]] = split_ids(row.get("writers"))

    principals: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(dataset_paths["title.principals.tsv.gz"]):
        if row["tconst"] in target_ids:
            principals[row["tconst"]].append({key: clean(value) for key, value in row.items()})

    people_ids = {person for values in list(crew_directors.values()) + list(crew_writers.values()) for person in values}
    people_ids.update(row["nconst"] for items in principals.values() for row in items if row.get("nconst"))
    names: dict[str, str] = {}
    for row in rows(dataset_paths["name.basics.tsv.gz"]):
        if row["nconst"] in people_ids:
            names[row["nconst"]] = clean(row.get("primaryName"))

    output_rows: list[dict[str, str]] = []
    credit_rows: list[dict[str, str]] = []
    for imdb_id, source in sources.items():
        film_rows = master_by_imdb.get(imdb_id, [])
        film = best_film(film_rows)
        animation_id = previous_ids.get(imdb_id, "")
        if not animation_id:
            animation_id = f"MUS-A-{next_id:06d}"
            next_id += 1

        seen = set()
        director_names: list[str] = []
        composer_names: list[str] = []
        cast_names: list[str] = []
        department_names: list[str] = []
        for category, person_ids in (("director", crew_directors.get(imdb_id, [])), ("writer", crew_writers.get(imdb_id, []))):
            for person_id in person_ids:
                person_name = names.get(person_id, "")
                if not person_name or (person_id, category, "") in seen:
                    continue
                seen.add((person_id, category, ""))
                credit_rows.append({"animation_id": animation_id, "imdb_id": imdb_id, "person_imdb_id": person_id, "person_name": person_name, "credit_group": "ساخت انیمیشن", "role": ROLE_LABELS[category], "imdb_category": category, "job": "", "characters": "", "ordering": "", "source_url": SOURCE_URL})
                if category == "director":
                    append_name(director_names, person_name)

        for principal in sorted(principals.get(imdb_id, []), key=lambda row: int(row.get("ordering") or 999)):
            person_id = principal.get("nconst", "")
            person_name = names.get(person_id, "")
            category = principal.get("category", "")
            job = principal.get("job", "")
            if not person_name:
                continue
            is_animation = bool(ANIMATION_TERMS.search(job))
            group = "دپارتمان انیمیشن" if is_animation else ("صداپیشگان و بازیگران" if category in {"actor", "actress"} else ("دپارتمان موسیقی" if category == "composer" else "عوامل اصلی"))
            role = job or ROLE_LABELS.get(category, category or "عامل")
            key = (person_id, category, job)
            if key not in seen:
                seen.add(key)
                credit_rows.append({"animation_id": animation_id, "imdb_id": imdb_id, "person_imdb_id": person_id, "person_name": person_name, "credit_group": group, "role": role, "imdb_category": category, "job": job, "characters": principal.get("characters", ""), "ordering": principal.get("ordering", ""), "source_url": SOURCE_URL})
            if category == "director": append_name(director_names, person_name)
            if category == "composer": append_name(composer_names, person_name)
            if category in {"actor", "actress"}: append_name(cast_names, person_name)
            if is_animation: append_name(department_names, person_name)

        if not director_names:
            for name in re.split(r"\s*[;؛,]\s*|\s+&\s+", film.get("director") or source.get("director", "")):
                append_name(director_names, name.strip())
        if not composer_names:
            for name in re.split(r"\s*[;؛]\s*", film.get("composer", "")):
                append_name(composer_names, name.strip())
        if not cast_names:
            for name in re.split(r"\s*[;؛]\s*", film.get("actors", "")):
                append_name(cast_names, name.strip())

        title = source.get("title") or film.get("title", "")
        year = re.sub(r"\.0$", "", source.get("year") or film.get("year", ""))
        genres = (source.get("imdb_genres") or "").replace(",", ";")
        output_rows.append({
            "animation_id": animation_id,
            "film_id": film.get("film_id", ""),
            "linked_film_ids": "; ".join(dict.fromkeys(row.get("film_id", "") for row in film_rows if row.get("film_id"))),
            "title": title,
            "persian_title": source.get("persian_title") or film.get("persian_title", ""),
            "year": year,
            "director": "; ".join(director_names),
            "country": film.get("country", "") or source.get("country", ""),
            "imdb_id": imdb_id,
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/",
            "imdb_genres": genres,
            "imdb_type": source.get("imdb_type", "movie"),
            "runtime_minutes": source.get("runtime_minutes", ""),
            "imdb_rating": source.get("imdb_rating", ""),
            "imdb_votes": source.get("imdb_votes", ""),
            "composer": "; ".join(composer_names),
            "voice_cast": "; ".join(cast_names),
            "animation_department": "; ".join(department_names),
            "source_scope": source.get("source_scope", ""),
            "selection_basis": "برچسب رسمی Animation در IMDb؛ از ۳۰نما فقط نوع movie",
            "thirtynama_id": source.get("thirtynama_id", "") or film.get("thirtynama_id", ""),
            "thirtynama_url": source.get("thirtynama_url", "") or film.get("thirtynama_url", ""),
            "downloadroz_search_url": f"https://tracy.ingmar-bergman.com/search/?s={quote_plus(title)}",
            "letterboxd_url": film.get("letterboxd_url", ""),
            "wikipedia_url": film.get("wikipedia_url", ""),
            "spotify_uri": film.get("spotify_uri", ""),
            "credit_source": SOURCE_URL,
        })

    output_rows.sort(key=lambda row: int(row["animation_id"].rsplit("-", 1)[1]))
    credit_rows.sort(key=lambda row: (row["animation_id"], row["credit_group"], int(row["ordering"] or 0), row["person_name"]))
    write_csv(OUTPUT, list(output_rows[0]), output_rows)
    write_csv(PUBLIC / "downloads" / "animations_all.csv", list(output_rows[0]), output_rows)
    write_csv(CREDITS, list(credit_rows[0]), credit_rows)
    write_csv(PUBLIC / "downloads" / "animation_credits.csv", list(credit_rows[0]), credit_rows)

    # Keep the general film list and the standalone animation catalogue in sync.
    format_rows = read_csv(FORMATS)
    format_pairs = {(row.get("film_id", ""), row.get("format", "")) for row in format_rows}
    for row in output_rows:
        for film_id in (part.strip() for part in row.get("linked_film_ids", "").split(";")):
            if film_id and (film_id, "انیمیشن") not in format_pairs:
                format_rows.append({"film_id": film_id, "format": "انیمیشن"})
                format_pairs.add((film_id, "انیمیشن"))
    format_rows.sort(key=lambda row: (row.get("film_id", ""), row.get("format", "")))
    write_csv(FORMATS, ["film_id", "format"], format_rows)
    report = {
        "animations": len(output_rows),
        "existing_inventory": sum(row["source_scope"] == "موجودی پیشین درگاه" for row in output_rows),
        "new_30nama_features": sum(row["source_scope"] == "افزوده از انیمیشن بلند ۳۰نما" for row in output_rows),
        "with_director": sum(bool(row["director"]) for row in output_rows),
        "with_composer": sum(bool(row["composer"]) for row in output_rows),
        "with_voice_cast": sum(bool(row["voice_cast"]) for row in output_rows),
        "credit_relations": len(credit_rows),
    }
    (PUBLIC / "animation_enrichment_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert len(output_rows) == 274 == len({row["imdb_id"] for row in output_rows})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
