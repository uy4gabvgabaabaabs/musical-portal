#!/usr/bin/env python3
"""Append verified films and retain full IMDb Music Department relations."""

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "public" / "musical_portal_4409.csv"
FILMS_SOURCE = Path(
    "/workspace/scratch/838e4f895c81/outputs/portal_import_336/"
    "درگاه_موزیکال_آماده_ورود_۳۳۶.csv"
)
RELATIONS_SOURCE = Path(
    "/workspace/scratch/838e4f895c81/outputs/portal_import_336/"
    "همکاری‌های_کامل_دپارتمان_موسیقی_۳۳۶_فیلم.csv"
)
RELATIONS_TARGET = ROOT / "public" / "music_department_relations_3516.csv"


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def main():
    portal_fields, portal_rows = read_rows(PORTAL)
    _, incoming_rows = read_rows(FILMS_SOURCE)
    relation_fields, relation_rows = read_rows(RELATIONS_SOURCE)

    existing_imdb_counts = Counter(
        row["imdb_id"].strip().lower() for row in portal_rows if row["imdb_id"].strip()
    )
    existing_by_imdb = {}
    for row in portal_rows:
        imdb = row["imdb_id"].strip().lower()
        if imdb and imdb not in existing_by_imdb:
            existing_by_imdb[imdb] = row
    existing_imdb = set(existing_by_imdb)
    incoming_imdb = [row["imdb_id"].strip().lower() for row in incoming_rows]
    duplicate_imdb = sorted(existing_imdb.intersection(incoming_imdb))
    if len(incoming_rows) != 336 or len(set(incoming_imdb)) != 336:
        raise RuntimeError("Incoming film package must contain 336 unique IMDb IDs")

    existing_ids = {row["film_id"] for row in portal_rows}
    new_source_rows = [
        row for row in incoming_rows if row["imdb_id"].strip().lower() not in existing_imdb
    ]
    incoming_ids = {row["film_id"] for row in new_source_rows}
    if existing_ids.intersection(incoming_ids):
        raise RuntimeError("Incoming film IDs collide with live portal IDs")

    people_fields = {
        "composer", "lyricist", "music_director", "arranger", "orchestrator",
        "vocal_arranger", "dance_arranger", "conductor", "musical_supervisor",
        "choreographer",
    }

    def merge_people(current, fresh):
        values = []
        seen = set()
        for source_value in (current, fresh):
            for value in source_value.split(";"):
                value = value.strip()
                key = value.casefold()
                if value and key not in seen:
                    seen.add(key)
                    values.append(value)
        return "; ".join(values)

    for source in incoming_rows:
        imdb = source["imdb_id"].strip().lower()
        if imdb not in existing_by_imdb:
            continue
        target = existing_by_imdb[imdb]
        for field in portal_fields:
            fresh = source.get(field, "")
            if field in people_fields:
                target[field] = merge_people(target.get(field, ""), fresh)
            elif not target.get(field) and fresh:
                target[field] = fresh

    additions = []
    for source in new_source_rows:
        row = {field: source.get(field, "") for field in portal_fields}
        row["persian_title"] = source.get("persian_title") or source["title"]
        row["collection"] = source.get("collection") or "گسترش Movie Collector"
        additions.append(row)

    all_rows = portal_rows + additions
    if len(all_rows) != 4716:
        raise RuntimeError(f"Expected 4716 films after import, got {len(all_rows)}")
    if len({row["film_id"] for row in all_rows}) != len(all_rows):
        raise RuntimeError("Duplicate film_id after import")
    imdb_values = [row["imdb_id"].strip().lower() for row in all_rows if row["imdb_id"].strip()]
    after_imdb_counts = Counter(imdb_values)
    introduced_duplicates = [
        imdb for imdb, count in after_imdb_counts.items()
        if count > existing_imdb_counts.get(imdb, 0) and count > 1
    ]
    if introduced_duplicates:
        raise RuntimeError(f"Import introduced IMDb duplicates: {introduced_duplicates[:10]}")

    with PORTAL.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=portal_fields)
        writer.writeheader()
        writer.writerows(all_rows)

    incoming_by_id = {row["film_id"]: row for row in incoming_rows}
    id_remap = {}
    for source in incoming_rows:
        imdb = source["imdb_id"].strip().lower()
        if imdb in existing_by_imdb:
            id_remap[source["film_id"]] = existing_by_imdb[imdb]["film_id"]
    for relation in relation_rows:
        old_id = relation["film_id"]
        if old_id in id_remap:
            target = existing_by_imdb[incoming_by_id[old_id]["imdb_id"].strip().lower()]
            relation["film_id"] = target["film_id"]
            relation["title"] = target["title"]
            relation["year"] = target["year"]

    with RELATIONS_TARGET.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=relation_fields)
        writer.writeheader()
        writer.writerows(relation_rows)

    print(
        f"films_before={len(portal_rows)} duplicates_enriched={len(duplicate_imdb)} "
        f"films_added={len(additions)} films_after={len(all_rows)} "
        f"music_relations={len(relation_rows)}"
    )


if __name__ == "__main__":
    main()
