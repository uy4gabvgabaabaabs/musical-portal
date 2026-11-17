#!/usr/bin/env python3
"""Build a merged CSV export and a portable source backup for the portal."""

import argparse
import csv
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DOWNLOADS = PUBLIC / "downloads"


def read_csv(name: str):
    with (PUBLIC / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_complete_csv() -> Path:
    films = read_csv("musical_portal_4409.csv")
    genres = {row["film_id"]: row for row in read_csv("film_genres.csv")}
    formats = {row["film_id"]: row for row in read_csv("film_formats.csv")}
    styles = {row["film_id"]: row for row in read_csv("film_styles.csv")}
    base_fields = list(films[0])
    insert_at = base_fields.index("collection")
    fields = base_fields[:insert_at] + ["genre_1", "genre_2", "format", "style_1", "style_2"] + base_fields[insert_at:]
    output = DOWNLOADS / f"musical_portal_complete_{len(films)}.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for film in films:
            film_id = film["film_id"]
            row = dict(film)
            row.update({
                "genre_1": genres.get(film_id, {}).get("genre_1", ""),
                "genre_2": genres.get(film_id, {}).get("genre_2", ""),
                "format": formats.get(film_id, {}).get("format", ""),
                "style_1": styles.get(film_id, {}).get("style_1", ""),
                "style_2": styles.get(film_id, {}).get("style_2", ""),
            })
            writer.writerow(row)
    return output


def backup_note(version: str, film_count: int) -> str:
    return f"""# پشتیبان درگاه موزیکال — نسخهٔ {version}

این بسته شامل کدهای سایت، داده‌های پژوهشی، خروجی کامل {film_count} فیلم و فهرست‌های مستقل همهٔ مستندها، انیمیشن‌ها و فیلم‌های موسیقی‌محور است.

## فایل‌های داده

- `public/musical_portal_4409.csv`: جدول اصلی فیلم‌ها (نام پایدار قدیمی)
- `public/documentaries.csv`: جدول مستقل همهٔ مستندها با شناسهٔ `MUS-D`
- `public/documentary_credits.csv`: عوامل و دپارتمان موسیقی مستندها
- `public/documentary_subjects.csv`: شخصیت‌ها، گروه‌ها و Bandهای موضوع مستند
- `public/documentaries_excluded_concert_tour.csv`: موارد کنسرت/تور کنارگذاشته‌شده از این مسیر
- `public/animations.csv`: جدول مستقل انیمیشن‌ها با شناسهٔ `MUS-A`
- `public/animation_credits.csv`: کارگردان، آهنگ‌ساز، صداپیشه و عوامل اصلی انیمیشن‌ها
- `public/music_centered_films.csv`: ۶۰ فیلم موسیقی‌محور با شناسهٔ `MUS-MC` و اتصال IMDb به موجودی‌های اصلی
- `public/imdb_music_labels_report.json`: گزارش تطبیق رسمی `Music` و `Musical` در IMDb
- `public/music_groups.csv`: هویت‌های قطعی گروه و Band موسیقی
- `public/music_group_relations.csv`: اتصال گروه‌ها به فیلم‌ها و مستندها
- `public/merge_audit/`: دفتر کامل ادغام بی‌اتلاف IMDb و بازنویسی اتصال‌ها
- `public/music_department_relations_3516.csv`: اتصال کامل فیلم، شخص و سمت موسیقی
- `public/film_genres.csv`: گونه‌ها
- `public/film_formats.csv`: قالب‌ها
- `public/film_styles.csv`: سبک‌های موسیقایی
- `public/musical_numbers_572.csv`: شماره‌های موزیکال (نام پایدار قدیمی)
- `exports/musical_portal_complete_{film_count}.csv`: خروجی یکپارچه
- `exports/documentaries_all.csv`: خروجی مستقل همهٔ مستندها
- `exports/documentary_credits.csv`: خروجی عوامل مستندها
- `exports/documentary_subjects.csv`: خروجی موضوع‌ها و Bandها
- `exports/animations_all.csv`: خروجی مستقل همهٔ انیمیشن‌ها
- `exports/animation_credits.csv`: خروجی عوامل انیمیشن‌ها
- `exports/music_centered_films.csv`: خروجی مستقل فیلم‌های موسیقی‌محور

## حافظه و دستور کار

- `public/docs/musical-portal-guide.md`: شیوه‌نامه و وضعیت جاری
- `public/docs/musical-portal-history.md`: تاریخچهٔ اجرایی نسخه‌به‌نسخه
- `public/docs/musical-portal-operations.md`: دستور کار ادامه، اعتبارسنجی و بازیابی

برای انتقال داده‌ها، فایل پوشهٔ `exports` کافی است. برای اجرای دوبارهٔ سایت، Node.js 22 یا جدیدتر، `npm ci` و سپس `npm run build` لازم است. برای ساخت یک نسخهٔ مستقل روی میزبان دیگر، تنظیمات `.openai/hosting.json` باید با مقصد تازه جایگزین شود.
"""


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    blocked = {".git", "node_modules", "dist", ".next", ".sites-runtime", ".wrangler"}
    if any(part in blocked for part in relative.parts):
        return False
    if relative.parts[:2] == ("public", "downloads"):
        return False
    return path.is_file()


def build_backup(version: str, complete_csv: Path) -> Path:
    output = DOWNLOADS / f"musical_portal_backup_v{version}.zip"
    prefix = f"musical_portal_backup_v{version}"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if should_include(path):
                archive.write(path, f"{prefix}/{path.relative_to(ROOT)}")
        archive.write(complete_csv, f"{prefix}/exports/{complete_csv.name}")
        archive.write(PUBLIC / "downloads" / "documentaries_all.csv", f"{prefix}/exports/documentaries_all.csv")
        archive.write(PUBLIC / "downloads" / "documentary_credits.csv", f"{prefix}/exports/documentary_credits.csv")
        archive.write(PUBLIC / "downloads" / "documentary_subjects.csv", f"{prefix}/exports/documentary_subjects.csv")
        archive.write(PUBLIC / "downloads" / "animations_all.csv", f"{prefix}/exports/animations_all.csv")
        archive.write(PUBLIC / "downloads" / "animation_credits.csv", f"{prefix}/exports/animation_credits.csv")
        archive.write(PUBLIC / "downloads" / "music_centered_films.csv", f"{prefix}/exports/music_centered_films.csv")
        film_count = sum(1 for _ in (PUBLIC / "musical_portal_4409.csv").open(encoding="utf-8-sig")) - 1
        archive.writestr(f"{prefix}/BACKUP_INFO_FA.md", backup_note(version, film_count))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="39")
    args = parser.parse_args()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    complete_csv = build_complete_csv()
    backup = build_backup(args.version, complete_csv)
    print(complete_csv)
    print(backup)


if __name__ == "__main__":
    main()
