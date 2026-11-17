#!/usr/bin/env python3
"""Validate the reversible IMDb merge used by portal version 50."""

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def read(name: str):
    with (PUBLIC / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def imdb(row):
    match = re.search(r"tt\d{5,10}", f"{row.get('imdb_id', '')} {row.get('imdb_url', '')}", re.I)
    return match.group(0).lower() if match else ""


films = read("musical_portal_4409.csv")
film_ids = [row["film_id"] for row in films]
assert len(films) == 4571, f"expected 4571 films, found {len(films)}"
assert len(film_ids) == len(set(film_ids)), "film_id is not unique"

imdb_counts = Counter(imdb(row) for row in films if imdb(row))
assert not [identifier for identifier, count in imdb_counts.items() if count > 1], "duplicate IMDb IDs remain"

mapping = read("merge_audit/film_duplicate_mapping_v50.csv")
sources = read("merge_audit/film_duplicate_source_records_v50.csv")
rewrites = read("merge_audit/film_relation_rewrites_v50.csv")
assert len(mapping) == 237
assert len(sources) == 476
assert len(rewrites) == 434

by_imdb = {imdb(row): row for row in films if imdb(row)}
original_fields = [field for field in sources[0] if field not in {"normalized_imdb_id", "canonical_film_id", "original_source_row"}]
for source in sources:
    merged = by_imdb[source["normalized_imdb_id"]]
    preserved = json.loads(merged.get("merge_preserved_values_json", "") or "{}")
    for field in original_fields:
        value = source.get(field, "")
        assert not value or value == merged.get(field, "") or value in preserved.get(field, []), (
            source.get("film_id", ""), field, value
        )

valid_ids = set(film_ids)
for name in ("film_genres.csv", "film_formats.csv", "film_styles.csv"):
    rows = read(name)
    ids = [row["film_id"] for row in rows]
    assert len(ids) == len(set(ids)), f"duplicate relation ID in {name}"
    assert set(ids) <= valid_ids, f"orphan film relation in {name}"

print("merge validation passed")
