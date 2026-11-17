#!/usr/bin/env python3
"""Enrich the portal's documentary catalogue from IMDb TSV datasets.

The script downloads each dataset once, filters it by the portal's IMDb IDs,
and writes compact, auditable CSV relations. It performs no per-title API calls.
"""

import argparse
import csv
import gzip
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DOCUMENTARIES = PUBLIC / "documentaries.csv"
FILMS = PUBLIC / "musical_portal_4409.csv"
PORTAL_MUSIC_RELATIONS = PUBLIC / "music_department_relations_3516.csv"
DATASET_BASE = "https://datasets.imdbws.com"
DATASET_FILES = ("title.crew.tsv.gz", "title.principals.tsv.gz", "name.basics.tsv.gz")
SOURCE_URL = "https://developer.imdb.com/non-commercial-datasets/"

ROLE_LABELS = {
    "director": "کارگردان",
    "writer": "نویسنده",
    "composer": "آهنگساز",
    "producer": "تهیه‌کننده",
    "cinematographer": "فیلم‌بردار",
    "editor": "تدوینگر",
    "actor": "بازیگر",
    "actress": "بازیگر",
    "self": "حضور به‌عنوان خود",
    "archive_footage": "تصویر آرشیوی",
    "archive_sound": "صدای آرشیوی",
}
MUSIC_TERMS = re.compile(
    r"\b(music|musical|composer|composition|score|song|soundtrack|conductor|orchestr|arrang|lyric|vocal)\b",
    re.IGNORECASE,
)
GROUP_TERMS = re.compile(
    r"\b(band|group|orchestra|choir|ensemble|quartet|trio|collective|singers|themselves)\b",
    re.IGNORECASE,
)


def clean(value: str | None) -> str:
    return "" if not value or value == r"\N" else value.strip()


def split_ids(value: str | None) -> list[str]:
    return [item for item in clean(value).split(",") if item]


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def download(cache_dir: Path, filename: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    output = cache_dir / filename
    if output.exists() and output.stat().st_size > 1_000_000:
        print(f"reuse {filename} ({output.stat().st_size:,} bytes)", flush=True)
        return output
    temp = output.with_suffix(output.suffix + ".part")
    print(f"download {filename}", flush=True)
    subprocess.run(
        ["curl", "--fail", "--location", "--retry", "3", "--continue-at", "-", "--output", str(temp), f"{DATASET_BASE}/{filename}"],
        check=True,
    )
    temp.replace(output)
    return output


def rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def unique_names(ids: list[str], names: dict[str, dict[str, str]]) -> list[str]:
    seen = set()
    result = []
    for person_id in ids:
        name = clean(names.get(person_id, {}).get("primaryName"))
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            result.append(name)
    return result


def split_names(value: str) -> list[str]:
    return [name.strip() for name in re.split(r"\s*[;؛]\s*", clean(value)) if name.strip()]


def append_unique(values: list[str], value: str) -> None:
    if value and value.casefold() not in {item.casefold() for item in values}:
        values.append(value)


def subject_type(name: str, characters: str) -> str:
    evidence = f"{name} {characters}"
    if GROUP_TERMS.search(evidence):
        return "گروه یا Band"
    if "Self" in characters or "Himself" in characters or "Herself" in characters:
        return "شخصیت موسیقایی"
    return "شخص یا گروه"


def subject_confidence(title: str, name: str, ordering: int, genres: str) -> tuple[str, str, str]:
    title_norm, name_norm = normalize(title), normalize(name)
    name_tokens = [token for token in name_norm.split() if len(token) >= 4]
    exact = bool(name_norm and name_norm in title_norm)
    token_match = any(token in title_norm.split() for token in name_tokens)
    if exact or (token_match and ordering <= 3):
        return "موضوع اصلی پیشنهادی", "بالا", "نام شخص/گروه در عنوان"
    if "Biography" in genres.split(";") and ordering <= 3:
        return "موضوع اصلی پیشنهادی", "متوسط", "اعتبار اصلی در مستند زندگی‌نامه‌ای"
    if ordering <= 3:
        return "حضور محوری پیشنهادی", "متوسط", "اعتبار اصلی IMDb"
    return "حضور، مصاحبه یا آرشیو", "پایین", "اعتبار فرعی IMDb"


def write_csv(path: Path, fieldnames: list[str], output_rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/musical-portal-imdb"))
    args = parser.parse_args()

    with DOCUMENTARIES.open(encoding="utf-8-sig", newline="") as handle:
        documentary_reader = csv.DictReader(handle)
        documentary_fields = list(documentary_reader.fieldnames or [])
        documentaries = list(documentary_reader)
    by_imdb = {row["imdb_id"]: row for row in documentaries}
    by_documentary_id = {row["documentary_id"]: row for row in documentaries}
    target_ids = set(by_imdb)
    assert len(documentaries) == len(target_ids)

    dataset_paths = {filename: download(args.cache_dir, filename) for filename in DATASET_FILES}

    crew_directors: dict[str, list[str]] = {}
    crew_writers: dict[str, list[str]] = {}
    for row in rows(dataset_paths["title.crew.tsv.gz"]):
        imdb_id = row["tconst"]
        if imdb_id in target_ids:
            crew_directors[imdb_id] = split_ids(row.get("directors"))
            crew_writers[imdb_id] = split_ids(row.get("writers"))
    print(f"matched crew: {len(crew_directors)}/{len(target_ids)}", flush=True)

    principal_rows: list[dict[str, str]] = []
    for row in rows(dataset_paths["title.principals.tsv.gz"]):
        if row["tconst"] in target_ids:
            principal_rows.append({key: clean(value) for key, value in row.items()})
    print(f"matched principal rows: {len(principal_rows)}", flush=True)

    people_ids = {
        person_id
        for ids in list(crew_directors.values()) + list(crew_writers.values())
        for person_id in ids
    }
    people_ids.update(row["nconst"] for row in principal_rows if row.get("nconst"))
    names: dict[str, dict[str, str]] = {}
    for row in rows(dataset_paths["name.basics.tsv.gz"]):
        if row["nconst"] in people_ids:
            names[row["nconst"]] = {key: clean(value) for key, value in row.items()}
    print(f"matched people: {len(names)}/{len(people_ids)}", flush=True)

    principals_by_title: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in principal_rows:
        principals_by_title[row["tconst"]].append(row)

    credit_rows: list[dict[str, str]] = []
    subject_rows: list[dict[str, str]] = []
    directors_by_title: dict[str, list[str]] = defaultdict(list)
    composers_by_title: dict[str, list[str]] = defaultdict(list)
    music_department_by_title: dict[str, list[str]] = defaultdict(list)
    portal_music_names_by_title: dict[str, list[str]] = defaultdict(list)
    portal_composer_names_by_title: dict[str, list[str]] = defaultdict(list)
    subjects_by_title: dict[str, list[str]] = defaultdict(list)

    for imdb_id, documentary in by_imdb.items():
        documentary_id = documentary["documentary_id"]
        seen_credit_keys = set()

        for role, person_ids in (("director", crew_directors.get(imdb_id, [])), ("writer", crew_writers.get(imdb_id, []))):
            for person_id in person_ids:
                person = names.get(person_id, {})
                person_name = clean(person.get("primaryName"))
                if not person_name:
                    continue
                key = (person_id, role, "")
                if key in seen_credit_keys:
                    continue
                seen_credit_keys.add(key)
                credit_rows.append({
                    "documentary_id": documentary_id,
                    "imdb_id": imdb_id,
                    "person_imdb_id": person_id,
                    "person_name": person_name,
                    "credit_group": "ساخت فیلم",
                    "role": ROLE_LABELS[role],
                    "imdb_category": role,
                    "job": "",
                    "characters": "",
                    "ordering": "",
                    "source_url": SOURCE_URL,
                })
                if role == "director":
                    directors_by_title[imdb_id].append(person_id)

        for principal in sorted(principals_by_title.get(imdb_id, []), key=lambda row: int(row.get("ordering") or 999)):
            person_id = principal.get("nconst", "")
            person = names.get(person_id, {})
            person_name = clean(person.get("primaryName"))
            if not person_name:
                continue
            category = principal.get("category", "")
            job = principal.get("job", "")
            characters = principal.get("characters", "")
            ordering = int(principal.get("ordering") or 999)
            is_music = category == "composer" or bool(MUSIC_TERMS.search(job))
            credit_group = "دپارتمان موسیقی" if is_music else "عوامل و حضورهای اصلی"
            role = ROLE_LABELS.get(category, category or "عامل")
            if job:
                role = job
            key = (person_id, category, job)
            if key not in seen_credit_keys:
                seen_credit_keys.add(key)
                credit_rows.append({
                    "documentary_id": documentary_id,
                    "imdb_id": imdb_id,
                    "person_imdb_id": person_id,
                    "person_name": person_name,
                    "credit_group": credit_group,
                    "role": role,
                    "imdb_category": category,
                    "job": job,
                    "characters": characters,
                    "ordering": str(ordering),
                    "source_url": SOURCE_URL,
                })
            if category == "director" and person_id not in directors_by_title[imdb_id]:
                directors_by_title[imdb_id].append(person_id)
            if category == "composer" and person_id not in composers_by_title[imdb_id]:
                composers_by_title[imdb_id].append(person_id)
            if is_music and person_id not in music_department_by_title[imdb_id]:
                music_department_by_title[imdb_id].append(person_id)

            if category in {"self", "archive_footage", "archive_sound"}:
                relation, confidence, method = subject_confidence(
                    documentary["title"], person_name, ordering, documentary.get("imdb_genres", "")
                )
                subject_rows.append({
                    "documentary_id": documentary_id,
                    "imdb_id": imdb_id,
                    "subject_imdb_id": person_id,
                    "subject_name": person_name,
                    "subject_type": subject_type(person_name, characters),
                    "relation": relation,
                    "confidence": confidence,
                    "basis": method,
                    "imdb_category": category,
                    "characters": characters,
                    "ordering": str(ordering),
                    "source_url": SOURCE_URL,
                })
                if confidence in {"بالا", "متوسط"} and person_id not in subjects_by_title[imdb_id]:
                    subjects_by_title[imdb_id].append(person_id)

    with FILMS.open(encoding="utf-8-sig", newline="") as handle:
        portal_films = {row["film_id"]: row for row in csv.DictReader(handle)}
    portal_roles = {
        "composer": "آهنگ‌ساز موسیقی متن",
        "lyricist": "ترانه‌سرا",
        "music_director": "مدیر موسیقی",
        "arranger": "تنظیم‌کننده",
        "orchestrator": "ارکستراتور",
        "vocal_arranger": "تنظیم‌کنندهٔ آواز",
        "dance_arranger": "تنظیم‌کنندهٔ رقص",
        "conductor": "رهبر ارکستر",
        "musical_supervisor": "ناظر موسیقی",
    }
    seen_portal_credits = {(row["documentary_id"], row["person_name"].casefold(), row["role"].casefold()) for row in credit_rows}
    for documentary in documentaries:
        film = portal_films.get(documentary.get("film_id", ""), {})
        for field, role_fa in portal_roles.items():
            for person_name in split_names(film.get(field, "")):
                key = (documentary["documentary_id"], person_name.casefold(), role_fa.casefold())
                if key in seen_portal_credits:
                    continue
                seen_portal_credits.add(key)
                credit_rows.append({
                    "documentary_id": documentary["documentary_id"],
                    "imdb_id": documentary["imdb_id"],
                    "person_imdb_id": "",
                    "person_name": person_name,
                    "credit_group": "دپارتمان موسیقی",
                    "role": role_fa,
                    "imdb_category": field,
                    "job": role_fa,
                    "characters": "",
                    "ordering": "",
                    "source_url": documentary.get("imdb_url", ""),
                })
                append_unique(portal_music_names_by_title[documentary["imdb_id"]], person_name)
                if field == "composer":
                    append_unique(portal_composer_names_by_title[documentary["imdb_id"]], person_name)

    if PORTAL_MUSIC_RELATIONS.exists():
        documentary_by_film = {row["film_id"]: row for row in documentaries if row.get("film_id")}
        with PORTAL_MUSIC_RELATIONS.open(encoding="utf-8-sig", newline="") as handle:
            for relation in csv.DictReader(handle):
                documentary = documentary_by_film.get(relation.get("film_id", ""))
                if not documentary:
                    continue
                person_name = clean(relation.get("person"))
                role_fa = clean(relation.get("normalized_role_fa")) or clean(relation.get("exact_job"))
                key = (documentary["documentary_id"], person_name.casefold(), role_fa.casefold())
                if not person_name or key in seen_portal_credits:
                    continue
                seen_portal_credits.add(key)
                credit_rows.append({
                    "documentary_id": documentary["documentary_id"],
                    "imdb_id": documentary["imdb_id"],
                    "person_imdb_id": clean(relation.get("imdb_name_id")),
                    "person_name": person_name,
                    "credit_group": "دپارتمان موسیقی",
                    "role": role_fa,
                    "imdb_category": clean(relation.get("department")),
                    "job": clean(relation.get("exact_job")),
                    "characters": "",
                    "ordering": "",
                    "source_url": clean(relation.get("source_url")) or documentary.get("imdb_url", ""),
                })
                append_unique(portal_music_names_by_title[documentary["imdb_id"]], person_name)
                if relation.get("normalized_role") == "composer":
                    append_unique(portal_composer_names_by_title[documentary["imdb_id"]], person_name)

    credit_rows.sort(key=lambda row: (row["documentary_id"], row["credit_group"], int(row["ordering"] or 0), row["person_name"]))
    subject_rows.sort(key=lambda row: (row["documentary_id"], int(row["ordering"] or 999), row["subject_name"]))
    write_csv(PUBLIC / "documentary_credits.csv", list(credit_rows[0]), credit_rows)
    write_csv(PUBLIC / "documentary_subjects.csv", list(subject_rows[0]), subject_rows)

    added_fields = ["composer", "music_department", "subjects", "music_subjects", "credit_source"]
    for field in added_fields:
        if field not in documentary_fields:
            documentary_fields.append(field)
    for documentary in documentaries:
        imdb_id = documentary["imdb_id"]
        director_names = unique_names(directors_by_title[imdb_id], names)
        composer_names = unique_names(composers_by_title[imdb_id], names)
        for name in portal_composer_names_by_title[imdb_id]:
            append_unique(composer_names, name)
        department_names = unique_names(music_department_by_title[imdb_id], names)
        for name in portal_music_names_by_title[imdb_id]:
            append_unique(department_names, name)
        subject_names = unique_names(subjects_by_title[imdb_id], names)
        if director_names:
            documentary["director"] = "; ".join(director_names)
        documentary["composer"] = "; ".join(composer_names)
        documentary["music_department"] = "; ".join(department_names)
        documentary["subjects"] = "; ".join(subject_names)
        documentary["music_subjects"] = "; ".join(subject_names)
        documentary["credit_source"] = SOURCE_URL
    write_csv(DOCUMENTARIES, documentary_fields, documentaries)
    write_csv(PUBLIC / "downloads" / "documentaries_all.csv", documentary_fields, documentaries)
    write_csv(PUBLIC / "downloads" / "documentary_credits.csv", list(credit_rows[0]), credit_rows)
    write_csv(PUBLIC / "downloads" / "documentary_subjects.csv", list(subject_rows[0]), subject_rows)

    report = {
        "documentaries": len(documentaries),
        "with_director": sum(bool(row.get("director")) for row in documentaries),
        "with_composer": sum(bool(row.get("composer")) for row in documentaries),
        "with_music_department": sum(bool(row.get("music_department")) for row in documentaries),
        "with_subject_candidates": sum(bool(row.get("music_subjects")) for row in documentaries),
        "credit_relations": len(credit_rows),
        "subject_relations": len(subject_rows),
        "source": SOURCE_URL,
    }
    (PUBLIC / "documentary_enrichment_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
