#!/usr/bin/env python3
"""Build conservative documentary/animation labels without rewriting film data."""

import csv
from pathlib import Path


CSV_PATH = Path(__file__).resolve().parents[1] / "public" / "musical_portal_4409.csv"
OUTPUT_PATH = CSV_PATH.with_name("film_formats.csv")


def format_for(row: dict[str, str]) -> str:
    evidence = " ".join((row.get("collection", ""), row.get("note_path", "")))
    if "موزیکال مستند" in evidence or "/قالب/مستند/" in evidence:
        return "مستند"
    if "موزیکال انیمیشن" in evidence or "/قالب/انیمیشن/" in evidence:
        return "انیمیشن"
    return ""


with CSV_PATH.open(encoding="utf-8-sig", newline="") as source:
    rows = list(csv.DictReader(source))

labels = [
    {"film_id": row["film_id"], "format": label}
    for row in rows
    if (label := format_for(row))
]

with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=["film_id", "format"])
    writer.writeheader()
    writer.writerows(labels)
