#!/usr/bin/env python3
"""Curated nature-as-protagonist musical-film candidates."""
import csv, gzip
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILMS=ROOT/"public"/"musical_portal_4409.csv"
IMDB=Path("/tmp/title.basics.tsv.gz")
OUT=ROOT/"working_genres"/"nature_protagonist_candidates.csv"

ids={
"tt0059742","tt0047472","tt0048445","tt0064782","tt0046807","tt0187756","tt0052225",
"tt0242898","tt0029075","tt0049055","tt0190291","tt0038116","tt0056526","tt0062974",
"tt0038969","tt0061852","tt0110357","tt6105098","tt0029583","tt0053285","tt0114148",
"tt3521164","tt27419466","tt2294629","tt4520988","tt0120855","tt2357291","tt0366548",
"tt1402488","tt0084237","tt0032264","tt0074225","tt0032455","tt0120910","tt0070917",
"tt0050188","tt0045693","tt0367110","tt0059246","tt0050665","tt0041161","tt0050758",
"tt0286490","tt0097757","tt5971474","tt0082406","tt0111419","tt0114108","tt0070016",
"tt0110300","tt0102802","tt0028988","tt0086590",
}
special_film_ids={"vault:688","indian_core:0093"}  # Lagaan; Tarzan (1985), lacking IMDb ID
with FILMS.open(encoding="utf-8-sig",newline="") as f: films=list(csv.DictReader(f))
portal={x["imdb_id"] for x in films if x.get("imdb_id") in ids}
genres={}
with gzip.open(IMDB,"rt",encoding="utf-8",newline="") as f:
    for x in csv.DictReader(f,delimiter="\t"):
        if x["tconst"] in portal: genres[x["tconst"]]=x.get("genres","")
fields=["film_id","imdb_id","title","persian_title","year","director","country","imdb_genres","classification_evidence","proposed_genre_2","review_status","review_note"]
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in films:
        imdb=x.get("imdb_id","")
        if imdb not in portal and x["film_id"] not in special_film_ids: continue
        w.writerow({"film_id":x["film_id"],"imdb_id":imdb,"title":x["title"],"persian_title":x["persian_title"],"year":x["year"],"director":x["director"],"country":x["country"],"imdb_genres":genres.get(imdb,""),"classification_evidence":"بازبینی محتوایی: طبیعت نیروی فعال روایت و بیان موزیکال","proposed_genre_2":"طبیعت‌محور","review_status":"نامزد","review_note":"منظره زیبا کافی نیست؛ طبیعت، فصل، اقلیم یا حیوانات باید روایت را شکل دهند"})
