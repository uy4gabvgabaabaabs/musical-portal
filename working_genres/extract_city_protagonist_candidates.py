#!/usr/bin/env python3
"""Curated city-as-protagonist musical-film candidates."""
import csv, gzip
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILMS=ROOT/"public"/"musical_portal_4409.csv"
IMDB=Path("/tmp/title.basics.tsv.gz")
OUT=ROOT/"working_genres"/"city_protagonist_candidates.csv"

ids={
"tt0041716","tt0076451","tt0055614","tt3581652","tt1321510","tt3783958","tt0073440",
"tt0037059","tt0211508","tt0043278","tt0062873","tt0058450","tt0203009","tt0055278",
"tt0051658","tt0294870","tt8721424","tt0907657","tt3544112","tt0101605","tt1980929",
"tt0076666","tt0080716","tt1016075","tt0068327","tt0299658","tt0427327","tt0095270",
"tt0078504","tt0104990","tt0024034","tt0112553","tt1043451","tt2395469","tt1324059",
"tt0048140","tt0065054","tt2141751","tt3573598","tt0090585","tt0057093","tt0065421",
"tt0063385","tt0058331","tt0408236","tt0058385","tt0084865","tt1436562","tt2357291",
"tt2474024","tt0780521","tt0461770","tt0091419","tt0445922","tt0087089","tt0075249",
"tt1876451","tt0087957","tt0099691","tt1398426","tt0086946","tt0084904","tt0089444",
"tt0039655","tt1010048",  # New Orleans; Slumdog Millionaire / Mumbai
}
ids.discard("tt2357291")  # Rio 2 عمدتاً آمازون‌محور است، نه شهر ریو
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
        if imdb not in portal: continue
        w.writerow({"film_id":x["film_id"],"imdb_id":imdb,"title":x["title"],"persian_title":x["persian_title"],"year":x["year"],"director":x["director"],"country":x["country"],"imdb_genres":genres.get(imdb,""),"classification_evidence":"بازبینی محتوایی: شهر/محله و فرهنگ شهری سازنده روایت","proposed_genre_2":"شهرمحور","review_status":"نامزد","review_note":"شهر باید نیروی روایی و هویتی اثر باشد، نه صرفاً محل وقوع"})
