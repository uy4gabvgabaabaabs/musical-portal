#!/usr/bin/env python3
"""Import the reviewed gaps from Letterboxd's Top 250 Musical Films list."""

import csv
import html
import json
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
LIST_PAGES = [
    "https://letterboxd.com/official/list/top-250-musical-films/",
    "https://letterboxd.com/official/list/top-250-musical-films/page/2/",
    "https://letterboxd.com/official/list/top-250-musical-films/page/3/",
]

# These are music-centred films rather than entries for the main musical corpus.
MUSIC_CENTERED = {
    "Linda Linda Linda": "گروه موسیقی، تمرین و اجرای جمعی",
    "Kneecap": "هویت گروه، زبان و اجرای موسیقی",
    "Latin Blood – The Ballad of Ney Matogrosso": "زندگی موسیقایی، بدن و اجرا",
    "Scott Pilgrim vs. the World": "گروه موسیقی و سازمان ریتمیک روایت",
    "Velvet Goldmine": "گلم‌راک، هویت و اجرای موسیقی",
    "The Forty-Year-Old Version": "رپ، آفرینش و بازتعریف هویت هنری",
    "I'm Not There": "زندگی موسیقایی و ساختار چندپارهٔ هویت",
    "A Mighty Wind": "گروه‌های فولک و اجرای بازگشت",
    "8 Mile": "رپ، رقابت اجرایی و شکل‌گیری هویت",
    "The Rivals of Amziah King": "موسیقی، اجتماع و ساختمان روایت",
}

# Purely American narrative titles that are neither animation nor music-centred
# are intentionally left out under the portal's current global-strengthening policy.
EXCLUDED = {"Waiting for Guffman", "Lemonade Mouth"}
IMDB_OVERRIDES = {
    "West Indies: The Fugitive Slaves of Liberty": "tt0080125",
    "My Little Pony: Equestria Girls – Rainbow Rocks": "tt3529198",
    "Barbie as The Princess & the Pauper": "tt0426955",
    "Latin Blood – The Ballad of Ney Matogrosso": "tt35301431",
}

PERSIAN = {
    "Memories of Matsuko": "خاطرات ماتسوکو", "Pariyerum Perumal": "پری‌یروم پرومال",
    "Kannathil Muthamittal": "بوسه‌ای بر گونه", "West Indies: The Fugitive Slaves of Liberty": "هند غربی: بردگان فراری آزادی",
    "The Hole": "حفره", "Lagaan: Once Upon a Time in India": "لاگان: روزی روزگاری در هند",
    "Blood Wedding": "عروسی خون", "Ordinary Miracle": "معجزهٔ معمولی", "Kal Ho Naa Ho": "شاید فردایی نباشد",
    "Gulaal": "گولال", "Sita Ramam": "سیتا رامام", "Same Old Song": "همان ترانهٔ قدیمی",
    "Season of the Devil": "فصل شیطان", "Ulidavaru Kandanthe": "آن‌گونه که دیگران دیدند",
    "El amor brujo": "عشق جادوگر", "Chandramukhi": "چاندراموخی",
    "The Legend of the Stardust Brothers": "افسانهٔ برادران غبار ستاره‌ای",
    "Queens of Drama": "ملکه‌های درام", "Vikram": "ویکرام", "Golden Eighties": "دههٔ هشتاد طلایی",
}


def get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def read_csv(name):
    with (PUBLIC / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows, fields):
    with (PUBLIC / name).open("w", encoding="utf-8-sig", newline="") as handle:
        ending = "\r\n" if name == "music_centered_films.csv" else "\n"
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator=ending)
        writer.writeheader(); writer.writerows(rows)


def list_items():
    items = []
    pattern = re.compile(r'data-item-name="([^"]+)"[^>]+data-item-slug="([^"]+)"')
    for url in LIST_PAGES:
        for raw, slug in pattern.findall(get(url)):
            value = html.unescape(raw)
            match = re.match(r"^(.*) \((\d{4})\)$", value)
            if match:
                items.append({"title": match.group(1), "year": match.group(2), "slug": slug})
    return items


def metadata(item):
    page = get(f"https://letterboxd.com/film/{item['slug']}/")
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', page, re.S)
    raw = next((block for block in blocks if '"@type":"Movie"' in block or '"@type": "Movie"' in block), "")
    if not raw:
        raise RuntimeError(f"No movie metadata found for {item['slug']}")
    raw = html.unescape(raw)
    data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    item["director"] = "; ".join(x["name"] for x in data.get("director", []))
    item["country"] = "; ".join(x["name"] for x in data.get("countryOfOrigin", []))
    item["genres"] = data.get("genre", [])
    item["letterboxd_url"] = f"https://letterboxd.com/film/{item['slug']}/"
    return item


def next_id(rows, field, prefix):
    values = [int(m.group(1)) for row in rows if (m := re.match(re.escape(prefix) + r"(\d+)$", row.get(field, "")))]
    return max(values, default=0) + 1


def imdb_match(title, year):
    if title in IMDB_OVERRIDES: return IMDB_OVERRIDES[title]
    url = "https://v3.sg.media-imdb.com/suggestion/x/" + urllib.parse.quote(title) + ".json"
    data = json.loads(get(url))
    exact = [x for x in data.get("d", []) if x.get("l", "").casefold() == title.casefold() and str(x.get("y", x.get("yr", ""))).startswith(str(year))]
    if not exact:
        exact = [x for x in data.get("d", []) if x.get("l", "").casefold() == title.casefold()]
    return exact[0].get("id", "") if exact else ""


def enrich_imdb(rows, selector):
    targets = [row for row in rows if selector(row) and not row.get("imdb_id")]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(imdb_match, row["title"], row["year"]): row for row in targets}
        for future in as_completed(futures):
            row = futures[future]
            try: imdb_id = future.result()
            except Exception: imdb_id = ""
            if imdb_id:
                row["imdb_id"] = imdb_id
                row["imdb_url"] = f"https://www.imdb.com/title/{imdb_id}/"


def main():
    films = read_csv("musical_portal_4409.csv")
    animations = read_csv("animations.csv")
    centered = read_csv("music_centered_films.csv")
    film_fields, animation_fields, centered_fields = list(films[0]), list(animations[0]), list(centered[0])
    existing = {(r["title"].casefold(), r["year"]) for r in films + animations}
    centered_existing = {(r["title"].casefold(), r["year"]) for r in centered}

    # Correct the known source-year error.
    for row in films:
        if row["title"] == "Golden Eighties" and row["year"] == "1988": row["year"] = "1986"

    film_no = next_id(films, "film_id", "MUS-F-")
    animation_no = next_id(animations, "animation_id", "MUS-A-")
    centered_no = next_id(centered, "music_centered_id", "MUS-MC-")
    report = {"main": [], "animation": [], "music_centered": [], "excluded": []}

    for item in list_items():
        key = (item["title"].casefold(), item["year"])
        if key in existing or key in centered_existing or item["title"] == "Golden Eighties": continue
        item = metadata(item)
        title = item["title"]
        if "Animation" in item["genres"]:
            row = {field: "" for field in animation_fields}
            row.update({"animation_id": f"MUS-A-{animation_no:06d}", "title": title,
                        "persian_title": PERSIAN.get(title, title), "year": item["year"],
                        "director": item["director"], "country": item["country"],
                        "imdb_genres": ";".join(item["genres"]), "imdb_type": "movie",
                        "source_scope": "فهرست ۲۵۰ موزیکال برتر Letterboxd",
                        "selection_basis": "انیمیشن بلند واجد معیار اجرای آوازی فهرست Letterboxd",
                        "letterboxd_url": item["letterboxd_url"], "credit_source": item["letterboxd_url"]})
            animations.append(row); animation_no += 1; report["animation"].append(title)
        elif title in MUSIC_CENTERED:
            row = {field: "" for field in centered_fields}
            row.update({"music_centered_id": f"MUS-MC-{centered_no:06d}", "title": title,
                        "persian_title": PERSIAN.get(title, title), "year": item["year"],
                        "director": item["director"], "country": item["country"],
                        "music_axis": MUSIC_CENTERED[title],
                        "portal_status": "مستقل از فهرست‌های اصلی",
                        "downloadroz_search_url": "https://tracy.ingmar-bergman.com/search/?s=" + item["slug"].replace("-", "+")})
            centered.append(row); centered_no += 1; report["music_centered"].append(title)
        elif title in EXCLUDED or item["country"] in {"United States", "United States of America"}:
            report["excluded"].append(title)
        else:
            row = {field: "" for field in film_fields}
            row.update({"film_id": f"MUS-F-{film_no:06d}", "title": title,
                        "persian_title": PERSIAN.get(title, title), "year": item["year"],
                        "director": item["director"], "country": item["country"],
                        "collection": "Letterboxd Top 250 Musical؛ تقویت سینمای غیرآمریکایی",
                        "letterboxd_url": item["letterboxd_url"], "imdb_musical": "1",
                        "downloadroz_search_url": "https://tracy.ingmar-bergman.com/search/?s=" + item["slug"].replace("-", "+"),
                        "merge_source_record_count": "1"})
            films.append(row); film_no += 1; report["main"].append(title)

    enrich_imdb(films, lambda r: "Letterboxd Top 250 Musical" in r.get("collection", ""))
    enrich_imdb(animations, lambda r: r.get("source_scope") == "فهرست ۲۵۰ موزیکال برتر Letterboxd")
    enrich_imdb(centered, lambda r: int(r.get("music_centered_id", "MUS-MC-0").rsplit("-", 1)[-1]) > 60)
    write_csv("musical_portal_4409.csv", films, film_fields)
    write_csv("animations.csv", animations, animation_fields)
    write_csv("music_centered_films.csv", centered, centered_fields)
    (PUBLIC / "letterboxd_top250_import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: len(v) for k, v in report.items()}, ensure_ascii=False))


if __name__ == "__main__": main()
