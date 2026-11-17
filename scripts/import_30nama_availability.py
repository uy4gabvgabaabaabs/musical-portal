#!/usr/bin/env python3
"""Attach verified 30nama availability and DownloadRoz searches to portal films."""

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "public" / "musical_portal_4409.csv"
NEW_FIELDS = ["online_availability", "thirtynama_id", "thirtynama_url", "downloadroz_search_url"]


def imdb_id(value: str) -> str:
    match = re.search(r"tt\d+", value or "", re.IGNORECASE)
    return match.group(0).lower() if match else ""


def normalized_title(value: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", ascii_title)


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="30nama musical CSV")
    args = parser.parse_args()

    films, fields = read_csv(PORTAL)
    source, _ = read_csv(args.source)
    by_imdb = defaultdict(list)
    by_title_year = defaultdict(list)
    for index, film in enumerate(films):
        identifier = imdb_id(f"{film.get('imdb_id', '')} {film.get('imdb_url', '')}")
        if identifier:
            by_imdb[identifier].append(index)
        key = (normalized_title(film.get("title", "")), film.get("year", "").strip())
        if all(key):
            by_title_year[key].append(index)

    matched_source = 0
    updated_rows = set()
    for item in source:
        indices = by_imdb.get(imdb_id(item.get("imdb_id", "")), [])
        if not indices:
            key = (normalized_title(item.get("title", "")), item.get("year", "").strip())
            indices = by_title_year.get(key, [])
        if not indices:
            continue
        matched_source += 1
        source_id = item.get("thirtynama_id", "").strip()
        page_id = source_id[2:] if source_id.startswith("30") else source_id
        thirtynama_url = f"https://30nama.com/movie/{page_id}" if page_id else ""
        for index in indices:
            film = films[index]
            film.update({
                "online_availability": "موجود در ۳۰نما",
                "thirtynama_id": source_id,
                "thirtynama_url": thirtynama_url,
                "downloadroz_search_url": f"https://tracy.ingmar-bergman.com/search/?s={quote_plus(film.get('title', ''))}",
            })
            updated_rows.add(index)

    for field in NEW_FIELDS:
        if field not in fields:
            fields.append(field)
    with PORTAL.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(films)

    print(f"matched_source_records={matched_source}")
    print(f"updated_portal_rows={len(updated_rows)}")
    print(f"unmatched_source_records={len(source) - matched_source}")


if __name__ == "__main__":
    main()
