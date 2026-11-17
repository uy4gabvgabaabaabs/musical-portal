from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "public" / "musical_portal_4409.csv"
SOURCE = ROOT.parent / "films_COMPLETE_4409_SPOTIFY_ROUND2_FINAL.csv"

portal = pd.read_csv(PORTAL, dtype=str, keep_default_na=False)
source = pd.read_csv(SOURCE, dtype=str, keep_default_na=False)

assert len(portal) == len(source) == 4409
for column in ["title", "year", "imdb_id", "persian_title", "wikipedia_url"]:
    assert portal[column].equals(source[column]), f"row alignment failed: {column}"

before = portal.copy()
incoming = source["spotify_uri"].ne("")
portal.loc[incoming, "spotify_uri"] = source.loc[incoming, "spotify_uri"]

assert portal["film_id"].equals(before["film_id"])
assert portal.drop(columns=["spotify_uri"]).equals(before.drop(columns=["spotify_uri"]))
assert portal.loc[before["spotify_uri"].ne(""), "spotify_uri"].ne("").all()
assert portal.loc[portal["spotify_uri"].ne(""), "spotify_uri"].str.match(
    r"^spotify:album:[A-Za-z0-9]{22}$"
).all()

added = before["spotify_uri"].eq("") & portal["spotify_uri"].ne("")
assert int(added.sum()) == 147
assert int(portal["spotify_uri"].ne("").sum()) == 597

portal.to_csv(PORTAL, index=False, lineterminator="\r\n")
print(f"added={int(added.sum())}")
print(f"total={int(portal['spotify_uri'].ne('').sum())}")
