#!/usr/bin/env python3
"""Merge reviewed working tables into the portal's lightweight label files."""

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
WORKING = ROOT / "working_genres"
FILMS = PUBLIC / "musical_portal_4409.csv"

GENRE_FILES = {
    "comedy_candidates.csv": "کمدی",
    "drama_candidates.csv": "درام", "romance_candidates.csv": "رمانس",
    "crime_candidates.csv": "جنایی", "horror_candidates.csv": "وحشت",
    "scifi_candidates.csv": "افسانه علمی", "western_candidates.csv": "وسترن",
    "war_candidates.csv": "جنگی", "children_candidates.csv": "کودکانه",
    "teen_candidates.csv": "نوجوانانه", "adventure_candidates.csv": "ماجرایی",
    "action_event_candidates.csv": "حادثه‌ای", "sport_candidates.csv": "ورزشی",
    "spectacle_candidates.csv": "عظیم", "fantasy_candidates.csv": "فانتزی",
    "history_candidates.csv": "تاریخی", "mystery_candidates.csv": "اسرارآمیز",
    "biography_candidates.csv": "سرگذشتنامه‌ای",
    "social_issue_candidates.csv": "اجتماعیِ مسئله‌محور",
    "disaster_candidates.csv": "فاجعه", "profession_candidates.csv": "شغلی/حرفه‌ای",
    "road_candidates.csv": "جاده‌ای", "film_within_film_candidates.csv": "فیلم در فیلم",
    "political_candidates.csv": "سیاسی", "city_protagonist_candidates.csv": "شهرمحور",
    "nature_protagonist_candidates.csv": "طبیعت‌محور",
    "unrestrained_adult_candidates.csv": "بزرگسالِ بی‌پروا",
}

FORMAT_FILES = {
    "documentary_candidates.csv": "مستند",
    "animation_candidates.csv": "انیمیشن",
}

ORDER = [
    "کمدی", "درام", "رمانس", "جنایی", "وحشت", "افسانه علمی", "وسترن", "جنگی", "کودکانه",
    "نوجوانانه", "ماجرایی", "حادثه‌ای", "ورزشی", "عظیم", "فانتزی",
    "تاریخی", "اسرارآمیز", "سرگذشتنامه‌ای", "اجتماعیِ مسئله‌محور",
    "فاجعه", "شغلی/حرفه‌ای", "جاده‌ای", "فیلم در فیلم", "سیاسی",
    "شهرمحور", "طبیعت‌محور", "بزرگسالِ بی‌پروا",
]
rank = {label: index for index, label in enumerate(ORDER)}

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))
film_ids = {row["film_id"] for row in films}

genres = defaultdict(set)
for filename, label in GENRE_FILES.items():
    with (WORKING / filename).open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            film_id = row["film_id"]
            if film_id in film_ids and label:
                genres[film_id].add(label)

formats = defaultdict(set)
for filename, label in FORMAT_FILES.items():
    with (WORKING / filename).open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if row["film_id"] in film_ids:
                formats[row["film_id"]].add(label)

with (PUBLIC / "film_genres.csv").open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=["film_id", "genre_1", "genre_2"], lineterminator="\n")
    writer.writeheader()
    for film in films:
        labels = sorted(genres[film["film_id"]], key=lambda value: (rank.get(value, 999), value))
        writer.writerow({"film_id": film["film_id"], "genre_1": "موزیکال", "genre_2": "؛ ".join(labels)})

with (PUBLIC / "film_formats.csv").open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=["film_id", "format"], lineterminator="\n")
    writer.writeheader()
    for film in films:
        labels = [label for label in ("مستند", "انیمیشن") if label in formats[film["film_id"]]]
        if labels:
            writer.writerow({"film_id": film["film_id"], "format": "؛ ".join(labels)})

print(f"films={len(films)} genre_assignments={sum(map(len, genres.values()))}")
print(f"format_assignments={sum(map(len, formats.values()))}")
