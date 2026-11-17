#!/usr/bin/env python3
"""Build the independent, editorial music-centered film directory.

The directory is deliberately separate from the portal's primary film table.
IMDb title IDs are the only overlap key. New rows never mutate the film,
documentary, or animation inventories.
"""

import csv
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
WORKING_30NAMA = ROOT / "working_30nama" / "30nama-music-classified.csv"


# title, Persian title, year, director, IMDb ID, editorial axis
SEED = [
    ("The Music Room", "اتاق موسیقی", "1958", "Satyajit Ray", "tt0051792", "موسیقی در مرکز روایت"),
    ("The Burmese Harp", "چنگ برمه‌ای", "1956", "Kon Ichikawa", "tt0049012", "ساز، اجرا و کنش"),
    ("The Chronicle of Anna Magdalena Bach", "وقایع‌نامهٔ آنا ماگدالنا باخ", "1968", "Jean-Marie Straub; Danièle Huillet", "tt0062804", "آهنگ‌ساز و آفرینش موسیقی"),
    ("The Connection", "ارتباط", "1961", "Shirley Clarke", "tt0054763", "جاز و اجرای زنده"),
    ("All Night Long", "تمام شب", "1962", "Basil Dearden", "tt0054614", "جاز و اجرای زنده"),
    ("Autumn Sonata", "سونات پاییزی", "1978", "Ingmar Bergman", "tt0077711", "موسیقی، حافظه و رابطه"),
    ("Orchestra Rehearsal", "تمرین ارکستر", "1978", "Federico Fellini", "tt0079759", "گروه موسیقی و جامعه"),
    ("The Conductor", "رهبر ارکستر", "1980", "Andrzej Wajda", "tt0079090", "رهبر ارکستر و اجرا"),
    ("Diva", "دیوا", "1981", "Jean-Jacques Beineix", "tt0082269", "صدا، ضبط و اجرا"),
    ("Amadeus", "آمادئوس", "1984", "Miloš Forman", "tt0086879", "آهنگ‌ساز و آفرینش موسیقی"),
    ("The Music Teacher", "استاد موسیقی", "1988", "Gérard Corbiau", "tt0095606", "آموزش و اجرای موسیقی"),
    ("'Round Midnight", "نیمه‌شب", "1986", "Bertrand Tavernier", "tt0090557", "جاز و اجرای زنده"),
    ("Bird", "برد", "1988", "Clint Eastwood", "tt0094747", "موسیقی‌دان و زندگی"),
    ("Tous les matins du monde", "همهٔ صبح‌های جهان", "1991", "Alain Corneau", "tt0103110", "ساز، آموزش و آفرینش"),
    ("A Heart in Winter", "قلبی در زمستان", "1992", "Claude Sautet", "tt0105682", "ساز، اجرا و رابطه"),
    ("Thirty Two Short Films About Glenn Gould", "سی‌ودو فیلم کوتاه دربارهٔ گلن گولد", "1993", "François Girard", "tt0108328", "موسیقی‌دان و فرم فیلم"),
    ("The Piano", "پیانو", "1993", "Jane Campion", "tt0107822", "ساز به‌مثابهٔ صدا و شخصیت"),
    ("Sopyonje", "سوپیونجه", "1993", "Im Kwon-taek", "tt0108192", "سنت موسیقایی و هویت"),
    ("Farewell My Concubine", "بدرود محبوب من", "1993", "Chen Kaige", "tt0106332", "اجرا، سنت و تاریخ"),
    ("Immortal Beloved", "محبوب جاودان", "1994", "Bernard Rose", "tt0110116", "آهنگ‌ساز و آفرینش موسیقی"),
    ("Farinelli", "فارینلی", "1994", "Gérard Corbiau", "tt0109771", "صدا و اجرای اپرایی"),
    ("Shine", "درخشش", "1996", "Scott Hicks", "tt0117631", "نوازنده و اجرای موسیقی"),
    ("The Red Violin", "ویولن قرمز", "1998", "François Girard", "tt0120802", "ساز به‌مثابهٔ شخصیت"),
    ("The Legend of 1900", "افسانهٔ ۱۹۰۰", "1998", "Giuseppe Tornatore", "tt0120731", "نوازنده و اجرای موسیقی"),
    ("Hilary and Jackie", "هیلاری و جکی", "1998", "Anand Tucker", "tt0150915", "موسیقی‌دان و زندگی"),
    ("Sweet and Lowdown", "شیرین و حقیر", "1999", "Woody Allen", "tt0158371", "جاز و شخصیت"),
    ("The Piano Teacher", "معلم پیانو", "2001", "Michael Haneke", "tt0254686", "موسیقی، انضباط و روان"),
    ("Taking Sides", "جانبداری", "2001", "István Szabó", "tt0260414", "موسیقی‌دان، قدرت و سیاست"),
    ("Together", "با هم", "2002", "Chen Kaige", "tt0332639", "ساز، آموزش و اجرا"),
    ("The Pianist", "پیانیست", "2002", "Roman Polanski", "tt0253474", "موسیقی، هویت و بقا"),
    ("The Beat That My Heart Skipped", "ضربی که قلبم از دست داد", "2005", "Jacques Audiard", "tt0411270", "نوازندگی و دگرگونی شخصیت"),
    ("The Violin", "ویولن", "2005", "Francisco Vargas", "tt0451966", "ساز، حافظه و مقاومت"),
    ("Copying Beethoven", "رونویسی بتهوون", "2006", "Agnieszka Holland", "tt0424908", "آهنگ‌ساز و آفرینش موسیقی"),
    ("Four Minutes", "چهار دقیقه", "2006", "Chris Kraus", "tt0461694", "آموزش و اجرای موسیقی"),
    ("Control", "کنترل", "2007", "Anton Corbijn", "tt0421082", "موسیقی‌دان و زندگی"),
    ("Half Moon", "نیمه‌ماه", "2006", "Bahman Ghobadi", "tt0847050", "سفر، اجرا و هویت موسیقایی"),
    ("No One Knows About Persian Cats", "کسی از گربه‌های ایرانی خبر ندارد", "2009", "Bahman Ghobadi", "tt1426378", "خرده‌فرهنگ و تولید موسیقی"),
    ("A Late Quartet", "کوارتتی دیرهنگام", "2012", "Yaron Zilberman", "tt1226240", "گروه موسیقی و رابطه"),
    ("Inside Llewyn Davis", "درون لوین دیویس", "2013", "Joel Coen; Ethan Coen", "tt2042568", "موسیقی‌دان و زیست حرفه‌ای"),
    ("Whiplash", "ویپلش", "2014", "Damien Chazelle", "tt2582802", "آموزش، اجرا و وسواس"),
    ("Love & Mercy", "عشق و بخشش", "2014", "Bill Pohlad", "tt0903657", "آفرینش موسیقی و روان"),
    ("Félicité", "فلیسیته", "2017", "Alain Gomis", "tt5980798", "اجرا، جامعه و زندگی"),
    ("Sound of Metal", "صدای متال", "2019", "Darius Marder", "tt5363618", "شنیدن، فقدان و هویت"),
    ("The Disciple", "شاگرد", "2020", "Chaitanya Tamhane", "tt11423784", "سنت، آموزش و کمال‌طلبی"),
    ("Tár", "تار", "2022", "Todd Field", "tt14444726", "رهبری ارکستر، قدرت و اجرا"),
    ("The Silence", "سکوت", "1998", "Mohsen Makhmalbaf", "tt0152438", "شنیدن، ریتم و ادراک"),
    ("Santoori", "سنتوری", "2007", "Dariush Mehrjui", "tt0385277", "نوازنده، اجرا و زوال"),
    ("Youth", "جوانی", "2015", "Paolo Sorrentino", "tt3312830", "آهنگ‌ساز، حافظه و اجرا"),
    ("8½", "هشت‌ونیم", "1963", "Federico Fellini", "tt0056801", "موسیقی در سازمان صوری فیلم"),
    ("La Strada", "جاده", "1954", "Federico Fellini", "tt0047528", "موتیف موسیقایی و شخصیت"),
    ("Once Upon a Time in the West", "روزی روزگاری در غرب", "1968", "Sergio Leone", "tt0064116", "موسیقی در سازمان صوری فیلم"),
    ("2001: A Space Odyssey", "۲۰۰۱: یک ادیسهٔ فضایی", "1968", "Stanley Kubrick", "tt0062622", "موسیقی در سازمان صوری فیلم"),
    ("Death in Venice", "مرگ در ونیز", "1971", "Luchino Visconti", "tt0067445", "موسیقی، میل و حافظه"),
    ("A Clockwork Orange", "پرتقال کوکی", "1971", "Stanley Kubrick", "tt0066921", "موسیقی، شخصیت و خشونت"),
    ("India Song", "ترانهٔ هند", "1975", "Marguerite Duras", "tt0073166", "موسیقی در سازمان صوری فیلم"),
    ("Koyaanisqatsi", "کویانیس‌کاتسی", "1982", "Godfrey Reggio", "tt0085809", "موسیقی در سازمان صوری فیلم"),
    ("First Name: Carmen", "نام کوچک: کارمن", "1983", "Jean-Luc Godard", "tt0085297", "موسیقی، بدن و تدوین"),
    ("Mishima: A Life in Four Chapters", "میشیما: یک زندگی در چهار فصل", "1985", "Paul Schrader", "tt0089603", "موسیقی در سازمان صوری فیلم"),
    ("The Double Life of Véronique", "زندگی دوگانهٔ ورونیک", "1991", "Krzysztof Kieślowski", "tt0101765", "موسیقی، همزاد و جهان درونی"),
    ("Three Colors: Blue", "سه رنگ: آبی", "1993", "Krzysztof Kieślowski", "tt0108394", "موسیقی، حافظه و ساختمان روایت"),
]


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def by_imdb(rows):
    return {row.get("imdb_id", "").strip(): row for row in rows if row.get("imdb_id", "").strip()}


def main():
    films = by_imdb(read_csv(PUBLIC / "musical_portal_4409.csv"))
    documentaries = by_imdb(read_csv(PUBLIC / "documentaries.csv"))
    animations = by_imdb(read_csv(PUBLIC / "animations.csv"))
    thirtynama = by_imdb(read_csv(WORKING_30NAMA))

    imdb_ids = [row[4] for row in SEED]
    if len(imdb_ids) != len(set(imdb_ids)):
        raise SystemExit("Duplicate IMDb ID in music-centered seed")

    fields = [
        "music_centered_id", "title", "persian_title", "year", "director",
        "music_axis", "imdb_id", "imdb_url", "film_id", "documentary_id",
        "animation_id", "portal_status", "thirtynama_url", "downloadroz_search_url",
    ]
    output_rows = []
    for index, (title, persian_title, year, director, imdb_id, music_axis) in enumerate(SEED, start=1):
        film = films.get(imdb_id, {})
        documentary = documentaries.get(imdb_id, {})
        animation = animations.get(imdb_id, {})
        source_30nama = thirtynama.get(imdb_id, {})
        links = []
        if film:
            links.append("فیلم اصلی")
        if documentary:
            links.append("مستند")
        if animation:
            links.append("انیمیشن")
        status = "متصل به " + " و ".join(links) if links else "مستقل از فهرست‌های اصلی"
        output_rows.append({
            "music_centered_id": f"MUS-MC-{index:06d}",
            "title": title,
            "persian_title": persian_title,
            "year": year,
            "director": director,
            "music_axis": music_axis,
            "imdb_id": imdb_id,
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/",
            "film_id": film.get("film_id", ""),
            "documentary_id": documentary.get("documentary_id", ""),
            "animation_id": animation.get("animation_id", ""),
            "portal_status": status,
            "thirtynama_url": source_30nama.get("thirtynama_url", ""),
            "downloadroz_search_url": "https://downloadroz.ir/?s=" + quote_plus(title),
        })

    targets = [PUBLIC / "music_centered_films.csv", PUBLIC / "downloads" / "music_centered_films.csv"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(output_rows)

    existing_films = sum(bool(row["film_id"]) for row in output_rows)
    existing_docs = sum(bool(row["documentary_id"]) for row in output_rows)
    existing_animations = sum(bool(row["animation_id"]) for row in output_rows)
    independent = sum(not row["film_id"] and not row["documentary_id"] and not row["animation_id"] for row in output_rows)
    print(f"music-centered={len(output_rows)} film-links={existing_films} documentary-links={existing_docs} animation-links={existing_animations} independent={independent}")


if __name__ == "__main__":
    main()
