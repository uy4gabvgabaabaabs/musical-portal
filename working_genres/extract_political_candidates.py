#!/usr/bin/env python3
"""Build a strict political-film review table from Wikidata classifications."""
import csv, gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
WIKIDATA = Path("/tmp/wikidata_political_imdb.csv")
IMDB = Path("/tmp/title.basics.tsv.gz")
OUT = ROOT / "working_genres" / "political_candidates.csv"

with FILMS.open(encoding="utf-8-sig", newline="") as f: films=list(csv.DictReader(f))
with WIKIDATA.open(encoding="utf-8-sig", newline="") as f: ids={r["imdb"] for r in csv.DictReader(f)}
editorial_ids={
    "tt0023969",  # Duck Soup
    "tt0068327",  # Cabaret
    "tt0068156",  # 1776
    "tt0067093",  # Fiddler on the Roof
    "tt0073440",  # Nashville
    "tt0079261",  # Hair
    "tt0082661",  # Lili Marleen
    "tt0105316",  # Sarafina!
    "tt0116250",  # Evita
    "tt1707386",  # Les Miserables
    "tt8503618",  # Hamilton
    "tt11873472", # Neptune Frost
    "tt8178634",  # RRR
    "tt0405508",  # Rang De Basanti
    "tt0105271",  # Roja
    "tt0164538",  # Dil Se..
    "tt0109010",  # 1942: A Love Story
    "tt0178186",  # Aandhi
    "tt0054098",  # Mughal-e-Azam
}
ids |= editorial_ids
ids.discard("tt0070917")  # The Wicker Man: false positive for this taxonomy
editorial_film_ids={"vault:688"}  # Lagaan: IMDb ID missing in portal row
portal_ids={r["imdb_id"] for r in films if r.get("imdb_id") in ids}
genres={}
with gzip.open(IMDB,"rt",encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        if r["tconst"] in portal_ids: genres[r["tconst"]]=r.get("genres","")
fields=["film_id","imdb_id","title","persian_title","year","director","country","imdb_genres","classification_evidence","proposed_genre_2","review_status","review_note"]
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for x in films:
        imdb=x.get("imdb_id","")
        if imdb not in portal_ids and x["film_id"] not in editorial_film_ids: continue
        source=("بازبینی محتوایی: سیاست محور روایت" if imdb in editorial_ids or x["film_id"] in editorial_film_ids else "Wikidata: political film/drama/thriller")
        w.writerow({"film_id":x["film_id"],"imdb_id":imdb,"title":x["title"],"persian_title":x["persian_title"],"year":x["year"],"director":x["director"],"country":x["country"],"imdb_genres":genres.get(imdb,""),"classification_evidence":source,"proposed_genre_2":"سیاسی","review_status":"نامزد","review_note":"سیاست، حکومت، ایدئولوژی یا منازعه سیاسی باید محور روایت باشد"})
