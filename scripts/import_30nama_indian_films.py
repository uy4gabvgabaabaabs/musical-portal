#!/usr/bin/env python3
"""Keep the 30nama review queue and import verified Indian feature films."""

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
FILMS = PUBLIC / "musical_portal_4409.csv"
REVIEW_DIR = ROOT / "working_30nama"

KNOWN_EXISTING_ALIASES = {
    "tt0169102": "vault:688",       # Lagaan: Once Upon a Time in India
    "tt0078204": "vault:519",       # Satyam Shivam Sundaram: Love Sublime
    "tt0150992": "vault:660",       # Straight from the Heart / Hum Dil De Chuke Sanam
    "tt0054073": "indian_core:0011", # The Cloud-Capped Star / Meghe Dhaka Tara
}

GENRE_FA = {
    "Action": "اکشن",
    "Adventure": "ماجراجویی",
    "Biography": "زندگی‌نامه‌ای",
    "Comedy": "کمدی",
    "Crime": "جنایی",
    "Drama": "درام",
    "Family": "خانوادگی",
    "Fantasy": "فانتزی",
    "History": "تاریخی",
    "Horror": "وحشت",
    "Music": "موسیقی",
    "Mystery": "معمایی",
    "Romance": "عاشقانه",
    "Sport": "ورزشی",
    "Thriller": "دلهره‌آور",
}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def imdb_id(value):
    match = re.search(r"tt\d+", value or "", re.I)
    return match.group(0).lower() if match else ""


def normalize(value):
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()
    value = value.replace("&", " and ")
    value = re.sub(r"\b(the|a|an)\b", " ", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def values(connection):
    result = []
    for edge in ((connection or {}).get("edges") or []):
        text = (((edge.get("node") or {}).get("name") or {}).get("nameText") or {}).get("text", "")
        if text and text not in result:
            result.append(text)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--credits", required=True)
    args = parser.parse_args()

    source, _ = read_csv(args.catalog)
    films, film_fields = read_csv(FILMS)
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    credits = json.loads(Path(args.credits).read_text(encoding="utf-8"))
    by_imdb = {imdb_id(row.get("imdb_id", "") + " " + row.get("imdb_url", "")) for row in films}
    by_title_year = {
        (normalize(row.get("title", "")), row.get("year", ""))
        for row in films
        if normalize(row.get("title", "")) and row.get("year", "")
    }

    queue = []
    for row in source:
        identifier = row.get("imdb_id", "")
        title_year = (normalize(row.get("title", "")), row.get("year", ""))
        title_year_match = all(title_year) and title_year in by_title_year
        if ((identifier and identifier in by_imdb) or title_year_match) and identifier not in KNOWN_EXISTING_ALIASES:
            continue
        info = (metadata.get(identifier) or {}).get("imdb") or {}
        countries = [item.get("id", "") for item in ((info.get("countriesOfOrigin") or {}).get("countries") or [])]
        genres = [item.get("id", "") for item in ((info.get("genres") or {}).get("genres") or [])]
        title_type = (info.get("titleType") or {}).get("id", "")
        is_indian_feature = "IN" in countries and title_type == "movie" and "Animation" not in genres
        if identifier in KNOWN_EXISTING_ALIASES:
            decision = "اتصال شد به رکورد موجود"
        elif is_indian_feature:
            decision = "افزوده شد: فیلم هندی غیرانیمیشن"
        elif "Animation" in genres:
            decision = "کنار گذاشته شد: انیمیشن"
        elif title_type and title_type != "movie":
            decision = "کنار گذاشته شد: قالب غیرسینمایی"
        elif not identifier:
            decision = "صف بررسی: بدون IMDb"
        else:
            decision = "صف بررسی: کشور/محتوا"
        page_id = row.get("thirtynama_id", "")
        if page_id.startswith("30"):
            page_id = page_id[2:]
        queue.append({
            "title": row.get("title", ""),
            "year_30nama": row.get("year", ""),
            "imdb_id": identifier,
            "imdb_year": str(((info.get("releaseYear") or {}).get("year") or "")),
            "countries": ";".join(countries),
            "title_type": title_type,
            "genres": ";".join(genres),
            "thirtynama_url": f"https://30nama.com/movie/{page_id}" if page_id else "",
            "decision": decision,
        })

    review_fields = ["title", "year_30nama", "imdb_id", "imdb_year", "countries", "title_type", "genres", "thirtynama_url", "decision"]
    write_csv(REVIEW_DIR / "30nama_unmatched_review.csv", queue, review_fields)

    indian = [row for row in queue if row["decision"].startswith("افزوده شد")]
    existing_ids = {row["film_id"] for row in films}
    numeric_ids = [int(match.group(1)) for value in existing_ids if (match := re.fullmatch(r"MUS-F-(\d+)", value))]
    next_id = max(numeric_ids) + 1
    new_films = []
    new_genres = []
    new_formats = []
    new_styles = []
    source_by_imdb = {row.get("imdb_id", ""): row for row in source if row.get("imdb_id")}

    films_by_id = {row["film_id"]: row for row in films}
    for identifier, film_id in KNOWN_EXISTING_ALIASES.items():
        if identifier not in source_by_imdb or film_id not in films_by_id:
            continue
        film = films_by_id[film_id]
        source_row = source_by_imdb[identifier]
        raw_30nama_id = source_row.get("thirtynama_id", "")
        page_id = raw_30nama_id[2:] if raw_30nama_id.startswith("30") else raw_30nama_id
        film.update({
            "imdb_id": identifier,
            "imdb_url": f"https://www.imdb.com/title/{identifier}/",
            "online_availability": "موجود در ۳۰نما",
            "thirtynama_id": raw_30nama_id,
            "thirtynama_url": f"https://30nama.com/movie/{page_id}" if page_id else "",
            "downloadroz_search_url": f"https://tracy.ingmar-bergman.com/search/?s={quote_plus(film.get('title', ''))}",
        })

    for item in indian:
        identifier = item["imdb_id"]
        packed = credits[identifier]
        info = packed.get("imdb") or {}
        credit = packed.get("credits") or {}
        source_row = source_by_imdb[identifier]
        title = ((info.get("titleText") or {}).get("text") or source_row.get("title") or "").strip()
        year = str(((info.get("releaseYear") or {}).get("year") or source_row.get("year") or ""))
        raw_30nama_id = source_row.get("thirtynama_id", "")
        page_id = raw_30nama_id[2:] if raw_30nama_id.startswith("30") else raw_30nama_id
        film_id = f"MUS-F-{next_id:06d}"
        next_id += 1
        new_films.append({
            "film_id": film_id,
            "title": title,
            "persian_title": title,
            "year": year,
            "director": "; ".join(values(credit.get("directors"))),
            "country": "هند",
            "collection": "۳۰نما؛ فیلم‌های هند",
            "actors": "; ".join(values(credit.get("stars"))),
            "composer": "; ".join(values(credit.get("composers"))),
            "imdb_id": identifier,
            "imdb_url": f"https://www.imdb.com/title/{identifier}/",
            "online_availability": "موجود در ۳۰نما",
            "thirtynama_id": raw_30nama_id,
            "thirtynama_url": f"https://30nama.com/movie/{page_id}" if page_id else "",
            "downloadroz_search_url": f"https://tracy.ingmar-bergman.com/search/?s={quote_plus(title)}",
        })
        imdb_genres = [genre for genre in item["genres"].split(";") if genre and genre != "Musical"]
        secondary = "؛ ".join(GENRE_FA[genre] for genre in imdb_genres if genre in GENRE_FA)
        new_genres.append({"film_id": film_id, "genre_1": "موزیکال", "genre_2": secondary})
        new_formats.append({"film_id": film_id, "format": "فیلم بلند"})
        new_styles.append({"film_id": film_id, "style_1": "موسیقی فیلم هندی", "style_2": "ترانه و رقص سینمای هند"})

    films.extend(new_films)
    write_csv(FILMS, films, film_fields)
    for filename, additions in (
        ("film_genres.csv", new_genres),
        ("film_formats.csv", new_formats),
        ("film_styles.csv", new_styles),
    ):
        rows, fields = read_csv(PUBLIC / filename)
        rows.extend(additions)
        write_csv(PUBLIC / filename, rows, fields)

    print(f"review_queue={len(queue)}")
    print(f"indian_features_added={len(new_films)}")
    print(f"portal_total={len(films)}")


if __name__ == "__main__":
    main()
