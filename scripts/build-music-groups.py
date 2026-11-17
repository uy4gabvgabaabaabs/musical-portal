#!/usr/bin/env python3
"""Build a conservative music-group catalogue and its film/documentary links.

This script uses only the portal CSV files and IMDb's non-commercial datasets.
It deliberately keeps ambiguous people/collectives out of the confirmed table
and writes them to a separate review queue.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
WORKING = ROOT / "working_music_groups"
DATASET_BASE = "https://datasets.imdbws.com"

CONFIDENCE_RANK = {"پایین": 1, "متوسط": 2, "بالا": 3}
GROUP_NAME_TERMS = re.compile(
    r"\b(band|orchestra|choir|chorus|ensemble|quartet|quintet|sextet|trio|collective|singers)\b",
    re.IGNORECASE,
)
THEMSELVES = re.compile(r"\bthemselves\b", re.IGNORECASE)
NON_MUSIC_GROUP_TERMS = re.compile(
    r"\b(dancers?|ballet|puppets?|lindy hoppers?|jitterbugs?|dance troupe)\b",
    re.IGNORECASE,
)

FILM_ROLE_LABELS = {
    "actors": "حضور/بازی",
    "composer": "آهنگ‌ساز",
    "lyricist": "ترانه‌سرا",
    "music_director": "مدیر موسیقی",
    "arranger": "تنظیم‌کننده",
    "orchestrator": "ارکستراتور",
    "vocal_arranger": "تنظیم‌کنندهٔ آواز",
    "dance_arranger": "تنظیم‌کنندهٔ رقص",
    "conductor": "رهبر ارکستر",
    "musical_supervisor": "سرپرست موسیقی",
    "choreographer": "طراح رقص",
}

PRINCIPAL_LABELS = {
    "actor": "حضور/بازی",
    "actress": "حضور/بازی",
    "self": "حضور به‌عنوان خود گروه",
    "archive_footage": "تصویر آرشیوی",
    "archive_sound": "صدای آرشیوی",
    "composer": "آهنگ‌ساز",
    "music_department": "دپارتمان موسیقی",
    "soundtrack": "موسیقی/ترانه",
}


def clean(value: str | None) -> str:
    return "" if not value or value == r"\N" else value.strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def dataset(cache_dir: Path, filename: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / filename
    if path.exists() and path.stat().st_size > 1_000_000:
        print(f"reuse {filename} ({path.stat().st_size:,} bytes)", flush=True)
        return path
    partial = path.with_suffix(path.suffix + ".part")
    print(f"download {filename}", flush=True)
    subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--retry",
            "3",
            "--continue-at",
            "-",
            "--output",
            str(partial),
            f"{DATASET_BASE}/{filename}",
        ],
        check=True,
    )
    partial.replace(path)
    return path


def split_names(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"\s*[;؛]\s*", clean(value)) if item.strip()]


def group_id(imdb_id: str) -> str:
    return f"MUS-G-{imdb_id.removeprefix('nm')}"


def append_relation(
    relations: dict[tuple[str, str, str], dict[str, object]],
    *,
    imdb_id: str,
    name: str,
    work_type: str,
    work_id: str,
    work_imdb_id: str,
    title: str,
    persian_title: str,
    year: str,
    role: str,
    evidence: str,
    confidence: str,
) -> None:
    key = (imdb_id, work_type, work_id)
    item = relations.setdefault(
        key,
        {
            "group_id": group_id(imdb_id),
            "group_imdb_id": imdb_id,
            "group_name": name,
            "work_type": work_type,
            "work_id": work_id,
            "work_imdb_id": work_imdb_id,
            "title": title,
            "persian_title": persian_title,
            "year": year,
            "roles": set(),
            "evidence": set(),
            "confidence": confidence,
        },
    )
    item["roles"].add(role)
    item["evidence"].add(evidence)
    if CONFIDENCE_RANK.get(confidence, 0) > CONFIDENCE_RANK.get(str(item["confidence"]), 0):
        item["confidence"] = confidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/musical-portal-imdb"))
    args = parser.parse_args()

    films = read_csv(PUBLIC / "musical_portal_4409.csv")
    documentaries = read_csv(PUBLIC / "documentaries.csv")
    subjects = read_csv(PUBLIC / "documentary_subjects.csv")
    documentary_by_id = {row["documentary_id"]: row for row in documentaries}
    documentary_film_ids: set[str] = set()
    documentary_imdb_ids: set[str] = set()
    for row in documentaries:
        documentary_imdb_ids.add(clean(row.get("imdb_id")))
        documentary_film_ids.add(clean(row.get("film_id")))
        documentary_film_ids.update(split_names(row.get("linked_film_ids", "")))
    documentary_film_ids.discard("")
    documentary_imdb_ids.discard("")

    subject_rows_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    review_reasons: dict[str, set[str]] = defaultdict(set)
    names_by_id: dict[str, str] = {}

    for row in subjects:
        imdb_id = clean(row.get("subject_imdb_id"))
        documentary = documentary_by_id.get(row.get("documentary_id", ""))
        if not imdb_id or not documentary or documentary.get("documentary_scope") != "مستند موسیقایی":
            continue
        if row.get("confidence") not in {"بالا", "متوسط"}:
            continue
        if row.get("subject_type") != "گروه یا Band":
            continue
        names_by_id.setdefault(imdb_id, clean(row.get("subject_name")))
        subject_rows_by_id[imdb_id].append(row)

    confirmed_ids: set[str] = set()
    for imdb_id, rows in subject_rows_by_id.items():
        name = names_by_id[imdb_id]
        characters = " ".join(clean(row.get("characters")) for row in rows)
        if THEMSELVES.search(characters):
            confirmed_ids.add(imdb_id)
            review_reasons[imdb_id].add("اعتبار Themselves در IMDb")
        if GROUP_NAME_TERMS.search(name):
            confirmed_ids.add(imdb_id)
            review_reasons[imdb_id].add("نشانهٔ صریح گروه در نام")
        if imdb_id not in confirmed_ids:
            review_reasons[imdb_id].add("تشخیص گروه فقط از متن نقش؛ نیازمند بازبینی")

    relations: dict[tuple[str, str, str], dict[str, object]] = {}

    # Documentary links are already identity-safe and keyed by IMDb name ID.
    for imdb_id in confirmed_ids:
        name = names_by_id[imdb_id]
        for row in subject_rows_by_id[imdb_id]:
            documentary = documentary_by_id[row["documentary_id"]]
            append_relation(
                relations,
                imdb_id=imdb_id,
                name=name,
                work_type="مستند",
                work_id=documentary["documentary_id"],
                work_imdb_id=documentary.get("imdb_id", ""),
                title=documentary.get("title", ""),
                persian_title=documentary.get("persian_title", ""),
                year=documentary.get("year", ""),
                role=row.get("relation", "موضوع/حضور"),
                evidence=row.get("basis", "اعتبار IMDb"),
                confidence=row.get("confidence", "متوسط"),
            )

    # Existing portal credit columns provide quick, explicit film relations.
    name_to_id = {names_by_id[item].casefold(): item for item in confirmed_ids}
    for film in films:
        if film.get("film_id") in documentary_film_ids or clean(film.get("imdb_id")) in documentary_imdb_ids:
            continue
        for column, label in FILM_ROLE_LABELS.items():
            for name in split_names(film.get(column, "")):
                imdb_id = name_to_id.get(name.casefold())
                if not imdb_id:
                    continue
                append_relation(
                    relations,
                    imdb_id=imdb_id,
                    name=names_by_id[imdb_id],
                    work_type="فیلم",
                    work_id=film.get("film_id", ""),
                    work_imdb_id=film.get("imdb_id", ""),
                    title=film.get("title", ""),
                    persian_title=film.get("persian_title", ""),
                    year=film.get("year", ""),
                    role=label,
                    evidence=f"ستون {column} در پایگاه",
                    confidence="بالا",
                )

    # IMDb principals add ID-based links missed by spelling differences.
    principal_path = dataset(args.cache_dir, "title.principals.tsv.gz")
    film_by_imdb = {
        clean(row.get("imdb_id")): row
        for row in films
        if clean(row.get("imdb_id"))
        and row.get("film_id") not in documentary_film_ids
        and clean(row.get("imdb_id")) not in documentary_imdb_ids
    }
    target_titles = set(film_by_imdb)
    print(
        f"scan title.principals for {len(confirmed_ids):,} groups × {len(target_titles):,} portal titles",
        flush=True,
    )
    scanned = 0
    principal_hits = 0
    discovered_principals: list[dict[str, str]] = []
    with gzip.open(principal_path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            scanned += 1
            if scanned % 10_000_000 == 0:
                print(f"principals scanned {scanned:,}; hits {principal_hits:,}", flush=True)
            if row["tconst"] not in target_titles:
                continue
            characters = clean(row.get("characters"))
            if (
                row.get("category") in {"self", "archive_footage", "archive_sound"}
                and THEMSELVES.search(characters)
            ):
                discovered_principals.append(dict(row))
            if row["nconst"] not in confirmed_ids:
                continue
            film = film_by_imdb[row["tconst"]]
            category = clean(row.get("category"))
            role = PRINCIPAL_LABELS.get(category, category or "اعتبار اصلی")
            if characters and characters not in {"[]", r"\N"}:
                role = f"{role}: {characters}"
            append_relation(
                relations,
                imdb_id=row["nconst"],
                name=names_by_id[row["nconst"]],
                work_type="فیلم",
                work_id=film.get("film_id", ""),
                work_imdb_id=film.get("imdb_id", ""),
                title=film.get("title", ""),
                persian_title=film.get("persian_title", ""),
                year=film.get("year", ""),
                role=role,
                evidence="شناسهٔ دقیق گروه در title.principals IMDb",
                confidence="بالا",
            )
            principal_hits += 1

    # Discover real music groups that occur in portal films as "Themselves".
    # The plural character credit is strong group evidence; an IMDb music
    # profession or an explicit collective term in the name is also required.
    discovered_ids = {row["nconst"] for row in discovered_principals}
    discovered_names: dict[str, str] = {}
    discovered_professions: dict[str, set[str]] = {}
    if discovered_ids:
        names_path = dataset(args.cache_dir, "name.basics.tsv.gz")
        print(f"scan name.basics for {len(discovered_ids):,} plural-self candidates", flush=True)
        with gzip.open(names_path, "rt", encoding="utf-8", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle, delimiter="\t"), start=1):
                if index % 10_000_000 == 0:
                    print(f"names scanned {index:,}", flush=True)
                if row["nconst"] not in discovered_ids:
                    continue
                discovered_names[row["nconst"]] = clean(row.get("primaryName"))
                discovered_professions[row["nconst"]] = set(clean(row.get("primaryProfession")).split(","))

    music_professions = {"soundtrack", "composer", "music_department"}
    discovered_confirmed: set[str] = set()
    discovered_review: set[str] = set()
    for imdb_id in discovered_ids:
        name = discovered_names.get(imdb_id, "")
        professions = discovered_professions.get(imdb_id, set())
        if (
            name
            and not NON_MUSIC_GROUP_TERMS.search(name)
            and (GROUP_NAME_TERMS.search(name) or professions & music_professions)
        ):
            discovered_confirmed.add(imdb_id)
            confirmed_ids.add(imdb_id)
            names_by_id[imdb_id] = name
            review_reasons[imdb_id].add("حضور جمعی Themselves در فیلم درگاه")
            if professions & music_professions:
                review_reasons[imdb_id].add("حرفهٔ موسیقایی در IMDb")
            if GROUP_NAME_TERMS.search(name):
                review_reasons[imdb_id].add("نشانهٔ صریح گروه در نام")
        elif name:
            discovered_review.add(imdb_id)

    for row in discovered_principals:
        imdb_id = row["nconst"]
        if imdb_id not in discovered_confirmed:
            continue
        film = film_by_imdb[row["tconst"]]
        category = clean(row.get("category"))
        role = PRINCIPAL_LABELS.get(category, category or "اعتبار اصلی")
        characters = clean(row.get("characters"))
        if characters and characters not in {"[]", r"\N"}:
            role = f"{role}: {characters}"
        append_relation(
            relations,
            imdb_id=imdb_id,
            name=names_by_id[imdb_id],
            work_type="فیلم",
            work_id=film.get("film_id", ""),
            work_imdb_id=film.get("imdb_id", ""),
            title=film.get("title", ""),
            persian_title=film.get("persian_title", ""),
            year=film.get("year", ""),
            role=role,
            evidence="Themselves + حرفهٔ موسیقایی/نام گروه در IMDb",
            confidence="بالا",
        )

    relation_rows: list[dict[str, str]] = []
    film_counts: dict[str, set[str]] = defaultdict(set)
    documentary_counts: dict[str, set[str]] = defaultdict(set)
    for item in relations.values():
        row = dict(item)
        row["role"] = "; ".join(sorted(row.pop("roles")))
        row["evidence"] = "; ".join(sorted(row["evidence"]))
        relation_rows.append(row)
        target = film_counts if row["work_type"] == "فیلم" else documentary_counts
        target[row["group_imdb_id"]].add(row["work_id"])

    relation_rows.sort(
        key=lambda row: (
            row["group_name"].casefold(),
            0 if row["work_type"] == "فیلم" else 1,
            int(row["year"]) if row["year"].isdigit() else 9999,
            row["title"].casefold(),
        )
    )

    groups: list[dict[str, str]] = []
    for imdb_id in sorted(confirmed_ids, key=lambda item: names_by_id[item].casefold()):
        rows = subject_rows_by_id.get(imdb_id, [])
        groups.append(
            {
                "group_id": group_id(imdb_id),
                "imdb_id": imdb_id,
                "name": names_by_id[imdb_id],
                "identity_type": "گروه موسیقی / Band",
                "film_count": str(len(film_counts[imdb_id])),
                "documentary_count": str(len(documentary_counts[imdb_id])),
                "evidence": "; ".join(sorted(review_reasons[imdb_id])),
                "confidence": max(
                    (row.get("confidence", "") for row in rows),
                    key=lambda value: CONFIDENCE_RANK.get(value, 0),
                ) if rows else "بالا",
                "review_status": "تأیید خودکار محافظه‌کارانه",
                "imdb_url": f"https://www.imdb.com/name/{imdb_id}/",
                "source_url": "https://developer.imdb.com/non-commercial-datasets/",
            }
        )

    review_rows: list[dict[str, str]] = []
    for imdb_id in sorted(set(subject_rows_by_id) - confirmed_ids, key=lambda item: names_by_id[item].casefold()):
        rows = subject_rows_by_id[imdb_id]
        review_rows.append(
            {
                "imdb_id": imdb_id,
                "name": names_by_id[imdb_id],
                "documentary_count": str(len({row["documentary_id"] for row in rows})),
                "best_confidence": max(
                    (row.get("confidence", "") for row in rows),
                    key=lambda value: CONFIDENCE_RANK.get(value, 0),
                ),
                "characters": "; ".join(sorted({clean(row.get("characters")) for row in rows if clean(row.get("characters"))})),
                "review_reason": "; ".join(sorted(review_reasons[imdb_id])),
                "imdb_url": f"https://www.imdb.com/name/{imdb_id}/",
            }
        )

    for imdb_id in sorted(discovered_review, key=lambda item: discovered_names[item].casefold()):
        review_rows.append(
            {
                "imdb_id": imdb_id,
                "name": discovered_names[imdb_id],
                "documentary_count": "0",
                "best_confidence": "متوسط",
                "characters": "Themselves",
                "review_reason": (
                    "نام نشان‌دهندهٔ گروه رقص/نمایشی است؛ نیازمند بازبینی"
                    if NON_MUSIC_GROUP_TERMS.search(discovered_names[imdb_id])
                    else "حضور جمعی دارد اما حرفهٔ موسیقایی در IMDb تأیید نشد"
                ),
                "imdb_url": f"https://www.imdb.com/name/{imdb_id}/",
            }
        )

    write_csv(
        PUBLIC / "music_groups.csv",
        [
            "group_id",
            "imdb_id",
            "name",
            "identity_type",
            "film_count",
            "documentary_count",
            "evidence",
            "confidence",
            "review_status",
            "imdb_url",
            "source_url",
        ],
        groups,
    )
    write_csv(
        PUBLIC / "music_group_relations.csv",
        [
            "group_id",
            "group_imdb_id",
            "group_name",
            "work_type",
            "work_id",
            "work_imdb_id",
            "title",
            "persian_title",
            "year",
            "role",
            "evidence",
            "confidence",
        ],
        relation_rows,
    )
    write_csv(
        WORKING / "music_group_candidates_review.csv",
        [
            "imdb_id",
            "name",
            "documentary_count",
            "best_confidence",
            "characters",
            "review_reason",
            "imdb_url",
        ],
        review_rows,
    )

    report = {
        "confirmed_groups": len(groups),
        "confirmed_groups_with_films": sum(bool(film_counts[item]) for item in confirmed_ids),
        "confirmed_groups_with_documentaries": sum(bool(documentary_counts[item]) for item in confirmed_ids),
        "film_relations": sum(row["work_type"] == "فیلم" for row in relation_rows),
        "documentary_relations": sum(row["work_type"] == "مستند" for row in relation_rows),
        "review_candidates": len(review_rows),
        "principal_hits": principal_hits,
        "film_groups_discovered": len(discovered_confirmed),
        "plural_self_review_candidates": len(discovered_review),
        "principal_rows_scanned": scanned,
        "method": "IMDb non-commercial datasets + portal CSV; no AI calls",
    }
    (WORKING / "music_groups_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
