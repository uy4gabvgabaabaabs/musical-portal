import csv
from pathlib import Path

portal_path = Path("public/musical_portal_4409.csv")
source_path = Path("../films_COMPLETE_4409_PERSIAN_IMDB_COMPLETE.csv")

with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
    source_rows = list(csv.DictReader(handle))

imdb_by_id = {
    row["final_id"].strip(): (row.get("imdb_id", "").strip(), row.get("imdb_url", "").strip())
    for row in source_rows
}

with portal_path.open("r", encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    fieldnames = list(reader.fieldnames or [])
    portal_rows = list(reader)

assert len(portal_rows) == 4409
assert len(source_rows) == 4409
assert len({row["film_id"] for row in portal_rows}) == 4409

for column in ("imdb_id", "imdb_url"):
    if column not in fieldnames:
        fieldnames.append(column)

matched = 0
for row in portal_rows:
    imdb_id, imdb_url = imdb_by_id.get(row["film_id"].strip(), ("", ""))
    row["imdb_id"] = imdb_id
    row["imdb_url"] = imdb_url
    matched += bool(imdb_id)

with portal_path.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(portal_rows)

print(f"rows={len(portal_rows)} imdb_links={matched} missing={len(portal_rows)-matched}")
