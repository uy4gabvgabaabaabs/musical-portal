import csv
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "public" / "musical_portal_4409.csv"
WIKIDATA = Path("/tmp/wikidata_profession_imdb.csv")
IMDB = Path("/tmp/title.basics.tsv.gz")
OUT = ROOT / "working_genres" / "profession_candidates.csv"

ns = {"s": "http://www.w3.org/2005/sparql-results#"}
subjects = defaultdict(set)
accepted_professions = {
    "musician", "teacher", "nanny", "drummer", "child singer", "celebrity",
}
root = ET.parse(WIKIDATA).getroot()
for result in root.findall(".//s:result", ns):
    values = {}
    for binding in result.findall("s:binding", ns):
        node = next(iter(binding), None)
        if node is not None:
            values[binding.attrib["name"]] = node.text or ""
    imdb = values.get("imdb", "").strip()
    label = values.get("subjectLabel", "").strip()
    if imdb and label in accepted_professions:
        subjects[imdb].add(label)

with PORTAL.open(encoding="utf-8-sig", newline="") as f:
    portal = list(csv.DictReader(f))
needed = {r["imdb_id"] for r in portal if r["imdb_id"] in subjects}

imdb_genres = {}
with gzip.open(IMDB, "rt", encoding="utf-8", errors="replace") as f:
    rd = csv.DictReader(f, delimiter="\t")
    for r in rd:
        if r["tconst"] in needed:
            imdb_genres[r["tconst"]] = r["genres"].replace(",", ", ")

fields = ["film_id", "imdb_id", "title", "persian_title", "year", "director", "country",
          "imdb_genres", "profession_subjects", "evidence", "proposed_genre_2", "review_status", "review_note"]
rows = []
for r in portal:
    imdb = r["imdb_id"]
    if imdb not in subjects:
        continue
    rows.append({
        "film_id": r["film_id"], "imdb_id": imdb, "title": r["title"],
        "persian_title": r["persian_title"], "year": r["year"], "director": r["director"],
        "country": r["country"], "imdb_genres": imdb_genres.get(imdb, ""),
        "profession_subjects": "; ".join(sorted(subjects[imdb])),
        "evidence": "Wikidata main subject: occupation or subclass",
        "proposed_genre_2": "شغلی/حرفه‌ای", "review_status": "نامزد",
        "review_note": "شغل یا محیط حرفه‌ای باید محور اصلی روایت باشد؛ نیازمند بازبینی انسانی",
    })

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=fields)
    wr.writeheader(); wr.writerows(rows)
