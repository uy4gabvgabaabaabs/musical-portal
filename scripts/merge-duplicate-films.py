#!/usr/bin/env python3
"""Merge exact IMDb duplicate films without discarding source values or legacy IDs."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
MASTER = PUBLIC / "musical_portal_4409.csv"
AUDIT_DIR = PUBLIC / "merge_audit"
VERSION = "50"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def imdb_id(row: dict[str, str]) -> str:
    combined = f"{row.get('imdb_id', '')} {row.get('imdb_url', '')}"
    match = re.search(r"tt\d{5,10}", combined, flags=re.IGNORECASE)
    return match.group(0).lower() if match else ""


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value != ""))


def split_ids(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*;\s*", value or "") if part.strip()]


master_fields, films = read_csv(MASTER)
groups: dict[str, list[dict[str, str]]] = defaultdict(list)
for film in films:
    if identifier := imdb_id(film):
        groups[identifier].append(film)

duplicate_groups = {key: rows for key, rows in groups.items() if len(rows) > 1}
if not duplicate_groups:
    raise SystemExit("No duplicate IMDb groups found; nothing was changed.")


def canonical_sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    film_id = row.get("film_id", "")
    # lb: records are the historical portal core; vault: records are later imports.
    historical_core = 1 if film_id.startswith("lb:") else 0
    completeness = sum(bool(value) for value in row.values())
    return historical_core, completeness, film_id


aliases: dict[str, str] = {}
canonical_groups: dict[str, tuple[dict[str, str], list[dict[str, str]]]] = {}
for identifier, members in duplicate_groups.items():
    canonical = max(members, key=canonical_sort_key)
    canonical_id = canonical["film_id"]
    canonical_groups[identifier] = canonical, members
    for member in members:
        aliases[member["film_id"]] = canonical_id

extra_master_fields = [
    "legacy_film_ids",
    "merge_source_record_count",
    "merge_preserved_values_json",
]
output_master_fields = master_fields + [field for field in extra_master_fields if field not in master_fields]

merged_films: list[dict[str, str]] = []
source_audit: list[dict[str, str]] = []
mapping_audit: list[dict[str, str]] = []
seen_imdb: set[str] = set()

for source_row_number, film in enumerate(films, start=2):
    identifier = imdb_id(film)
    if identifier not in duplicate_groups:
        output = dict(film)
        output.setdefault("legacy_film_ids", "")
        output.setdefault("merge_source_record_count", "1")
        output.setdefault("merge_preserved_values_json", "")
        merged_films.append(output)
        continue
    if identifier in seen_imdb:
        continue
    seen_imdb.add(identifier)
    canonical, members = canonical_groups[identifier]
    output = dict(canonical)
    for field in master_fields:
        if not output.get(field, ""):
            output[field] = next((member.get(field, "") for member in members if member.get(field, "")), "")
    source_ids = [member["film_id"] for member in members]
    output["legacy_film_ids"] = "; ".join(source_id for source_id in source_ids if source_id != canonical["film_id"])
    output["merge_source_record_count"] = str(len(members))
    preserved = {
        field: unique([member.get(field, "") for member in members])
        for field in master_fields
        if len(unique([member.get(field, "") for member in members])) > 1
    }
    output["merge_preserved_values_json"] = json.dumps(preserved, ensure_ascii=False, separators=(",", ":"))
    merged_films.append(output)
    mapping_audit.append({
        "imdb_id": identifier,
        "canonical_film_id": canonical["film_id"],
        "legacy_film_ids": "; ".join(source_id for source_id in source_ids if source_id != canonical["film_id"]),
        "source_record_count": str(len(members)),
        "preserved_fields": "; ".join(preserved),
    })
    for member in members:
        original_row = films.index(member) + 2
        source_audit.append({
            "normalized_imdb_id": identifier,
            "canonical_film_id": canonical["film_id"],
            "original_source_row": str(original_row),
            **member,
        })

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
write_csv(MASTER, output_master_fields, merged_films)
write_csv(
    AUDIT_DIR / f"film_duplicate_mapping_v{VERSION}.csv",
    ["imdb_id", "canonical_film_id", "legacy_film_ids", "source_record_count", "preserved_fields"],
    mapping_audit,
)
write_csv(
    AUDIT_DIR / f"film_duplicate_source_records_v{VERSION}.csv",
    ["normalized_imdb_id", "canonical_film_id", "original_source_row"] + master_fields,
    source_audit,
)

relation_audit: list[dict[str, str]] = []


def audit_row(path: Path, source_row: int, row: dict[str, str], old_id: str, new_id: str, column: str) -> None:
    relation_audit.append({
        "source_file": str(path.relative_to(ROOT)),
        "source_row": str(source_row),
        "id_column": column,
        "original_film_id": old_id,
        "canonical_film_id": new_id,
        "original_row_json": json.dumps(row, ensure_ascii=False, separators=(",", ":")),
    })


def remap_file(path: Path) -> None:
    fields, rows = read_csv(path)
    if not rows:
        return
    output_fields = list(fields)
    for source_row, row in enumerate(rows, start=2):
        original = dict(row)
        if "film_id" in fields and row.get("film_id", "") in aliases:
            old = row["film_id"]
            new = aliases[old]
            if old != new:
                if "legacy_film_id" not in output_fields:
                    output_fields.append("legacy_film_id")
                row["legacy_film_id"] = old
                row["film_id"] = new
                audit_row(path, source_row, original, old, new, "film_id")
        if "work_id" in fields and row.get("work_id", "") in aliases:
            old = row["work_id"]
            new = aliases[old]
            if old != new:
                if "legacy_work_id" not in output_fields:
                    output_fields.append("legacy_work_id")
                row["legacy_work_id"] = old
                row["work_id"] = new
                audit_row(path, source_row, original, old, new, "work_id")
        if "linked_film_ids" in fields:
            old_ids = split_ids(row.get("linked_film_ids", ""))
            new_ids = unique([aliases.get(old_id, old_id) for old_id in old_ids])
            if old_ids != new_ids:
                if "legacy_linked_film_ids" not in output_fields:
                    output_fields.append("legacy_linked_film_ids")
                row["legacy_linked_film_ids"] = "; ".join(old_ids)
                row["linked_film_ids"] = "; ".join(new_ids)
                for old_id in old_ids:
                    new_id = aliases.get(old_id, old_id)
                    if old_id != new_id:
                        audit_row(path, source_row, original, old_id, new_id, "linked_film_ids")
    write_csv(path, output_fields, rows)


live_relation_files = [
    PUBLIC / "musical_numbers_572.csv",
    PUBLIC / "music_department_relations_3516.csv",
    PUBLIC / "film_youtube_first_50.csv",
    PUBLIC / "documentaries.csv",
    PUBLIC / "animations.csv",
    PUBLIC / "music_group_relations.csv",
    PUBLIC / "downloads" / "documentaries_all.csv",
    PUBLIC / "downloads" / "animations_all.csv",
]
for path in live_relation_files:
    if path.exists():
        remap_file(path)


def merge_classification(path: Path, value_fields: list[str]) -> None:
    fields, rows = read_csv(path)
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    order: list[str] = []
    for source_row, row in enumerate(rows, start=2):
        old = row.get("film_id", "")
        new = aliases.get(old, old)
        if old != new:
            audit_row(path, source_row, dict(row), old, new, "film_id")
        if new not in buckets:
            order.append(new)
        buckets[new].append(row)
    output: list[dict[str, str]] = []
    for film_id in order:
        members = buckets[film_id]
        row = {"film_id": film_id}
        for field in value_fields:
            values: list[str] = []
            for member in members:
                values.extend(part.strip() for part in re.split(r"\s*[؛;]\s*", member.get(field, "")) if part.strip())
            row[field] = "؛ ".join(unique(values))
        output.append(row)
    write_csv(path, fields, output)


merge_classification(PUBLIC / "film_genres.csv", ["genre_1", "genre_2"])
merge_classification(PUBLIC / "film_formats.csv", ["format"])
merge_classification(PUBLIC / "film_styles.csv", ["style_1", "style_2"])

write_csv(
    AUDIT_DIR / f"film_relation_rewrites_v{VERSION}.csv",
    ["source_file", "source_row", "id_column", "original_film_id", "canonical_film_id", "original_row_json"],
    relation_audit,
)

print(f"duplicate_groups={len(duplicate_groups)}")
print(f"source_duplicate_records={sum(len(rows) for rows in duplicate_groups.values())}")
print(f"merged_film_count={len(merged_films)}")
print(f"removed_duplicate_rows={len(films) - len(merged_films)}")
print(f"relation_rewrites={len(relation_audit)}")
