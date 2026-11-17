#!/usr/bin/env python3
"""Attach exact IMDb Music/Musical flags to the portal's film table.

The IMDb dataset is an external input and is deliberately not committed. The
two derived flags are stored in the portal CSV so the published site and its
portable exports do not need IMDb at runtime.
"""

import argparse
import csv
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
REPORT = ROOT / "public" / "imdb_music_labels_report.json"
IMDB_ID = re.compile(r"tt\d+")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("imdb_basics", type=Path, help="IMDb title.basics.tsv.gz")
    args = parser.parse_args()

    with FILMS.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        films = list(reader)
        fields = list(reader.fieldnames or [])

    target_ids = {
        row["imdb_id"]
        for row in films
        if IMDB_ID.fullmatch(row.get("imdb_id", ""))
    }
    genres_by_imdb: dict[str, set[str]] = {}
    with gzip.open(args.imdb_basics, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            imdb_id = row["tconst"]
            if imdb_id in target_ids:
                genres_by_imdb[imdb_id] = set(row.get("genres", "").split(","))

    for field in ("imdb_music", "imdb_musical"):
        if field in fields:
            fields.remove(field)
    insert_at = fields.index("imdb_url") + 1
    fields[insert_at:insert_at] = ["imdb_music", "imdb_musical"]

    for film in films:
        genres = genres_by_imdb.get(film.get("imdb_id", ""))
        film["imdb_music"] = "" if genres is None else ("1" if "Music" in genres else "0")
        film["imdb_musical"] = "" if genres is None else ("1" if "Musical" in genres else "0")

    with FILMS.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(films)

    music = sum(row["imdb_music"] == "1" for row in films)
    musical = sum(row["imdb_musical"] == "1" for row in films)
    both = sum(row["imdb_music"] == row["imdb_musical"] == "1" for row in films)
    report = {
        "portal_films": len(films),
        "portal_imdb_ids": len(target_ids),
        "matched_imdb_ids": len(genres_by_imdb),
        "imdb_music": music,
        "imdb_musical": musical,
        "both": both,
        "music_only": music - both,
        "musical_only": musical - both,
        "neither": sum(
            row["imdb_music"] == row["imdb_musical"] == "0" for row in films
        ),
        "unknown": sum(not row["imdb_music"] for row in films),
        "source": "IMDb Non-Commercial Datasets / title.basics.tsv.gz",
        "generated_on": "2026-08-22",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert report == {
        **report,
        "portal_films": 4571,
        "portal_imdb_ids": 4449,
        "matched_imdb_ids": 4447,
        "imdb_music": 1226,
        "imdb_musical": 2070,
        "both": 66,
        "music_only": 1160,
        "musical_only": 2004,
        "neither": 1217,
        "unknown": 124,
    }
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
