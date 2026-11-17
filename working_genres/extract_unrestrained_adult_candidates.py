#!/usr/bin/env python3
"""Curated sexually explicit / transgressive adult musical candidates."""
import csv, gzip
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILMS=ROOT/"public"/"musical_portal_4409.csv"
IMDB=Path("/tmp/title.basics.tsv.gz")
OUT=ROOT/"working_genres"/"unrestrained_adult_candidates.csv"

# IMDb id -> intensity band (not a legal or moral judgment)
levels={
"tt0074113":"صریح / نزدیک به پورنو",
"tt0074533":"اروتیک یا عریان",
"tt0075849":"اروتیک یا عریان",
"tt0080752":"بزرگسالِ مرزشکن",
"tt5278832":"اروتیک یا عریان",
"tt0411705":"صریح / نزدیک به پورنو",
"tt0368222":"بزرگسالِ مرزشکن",
"tt0248845":"بزرگسالِ مرزشکن",
"tt0114436":"اروتیک یا عریان",
"tt0073629":"بزرگسالِ مرزشکن",
"tt0073298":"اروتیک یا عریان",
"tt0097858":"بزرگسالِ مرزشکن",
"tt0158983":"بزرگسالِ مرزشکن",
"tt0152139":"اروتیک یا عریان",
"tt0080380":"بزرگسالِ مرزشکن",
}
special={"vault:519":"اروتیک یا عریان"}  # Satyam Shivam Sundaram, no IMDb id in portal row
with FILMS.open(encoding="utf-8-sig",newline="") as f: films=list(csv.DictReader(f))
portal=set(levels) & {x.get("imdb_id","") for x in films}
genres={}
with gzip.open(IMDB,"rt",encoding="utf-8",newline="") as f:
    for x in csv.DictReader(f,delimiter="\t"):
        if x["tconst"] in portal: genres[x["tconst"]]=x.get("genres","")
fields=["film_id","imdb_id","title","persian_title","year","director","country","imdb_genres","adult_intensity","classification_evidence","proposed_genre_2","review_status","review_note"]
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in films:
        imdb=x.get("imdb_id","")
        level=levels.get(imdb) or special.get(x["film_id"])
        if not level: continue
        evidence="IMDb: Adult + بازبینی محتوایی" if imdb=="tt0074113" else "بازبینی محتوایی"
        w.writerow({"film_id":x["film_id"],"imdb_id":imdb,"title":x["title"],"persian_title":x["persian_title"],"year":x["year"],"director":x["director"],"country":x["country"],"imdb_genres":genres.get(imdb,""),"adult_intensity":level,"classification_evidence":evidence,"proposed_genre_2":"بزرگسالِ بی‌پروا","review_status":"نامزد","review_note":"رده‌بندی توصیفی است؛ صرفاً وجود مضمون جنسی برای ورود کافی نیست"})
