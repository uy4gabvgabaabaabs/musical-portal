"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import GPTButton from "../gpt-button";

type MusicCenteredFilm = {
  music_centered_id: string;
  title: string;
  persian_title: string;
  year: string;
  director: string;
  country: string;
  music_axis: string;
  imdb_id: string;
  imdb_url: string;
  film_id: string;
  documentary_id: string;
  animation_id: string;
  portal_status: string;
  thirtynama_url: string;
  downloadroz_search_url: string;
};

const PAGE_SIZE = 36;

function parseCSV(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { cell += '"'; i++; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") i++;
      row.push(cell);
      if (row.some(Boolean)) rows.push(row);
      row = []; cell = "";
    } else cell += char;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const headers = rows.shift()?.map(value => value.replace(/^\uFEFF/, "")) ?? [];
  return rows.map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function prompt(item: MusicCenteredFilm) {
  return `این فیلم را برای مدخل «فیلم‌های موسیقی‌محور اما نه لزوماً موزیکال» در کتاب علیرضا کاوه تحلیل کن. توضیح بده موسیقی چگونه روایت، شخصیت، اجرا، حافظه یا ساختمان صوری فیلم را می‌سازد. مرز آن را با موزیکال و فیلمی که فقط موسیقی متن برجسته دارد روشن کن و اگر داده‌ای قطعی نیست حدس نزن.\n\nTitle: ${item.title}\nYear: ${item.year}\nDirector: ${item.director}\nCountry: ${item.country || "—"}\nEditorial axis: ${item.music_axis}\nIMDb: ${item.imdb_id}`;
}

export default function MusicCenteredDirectory() {
  const [data, setData] = useState<MusicCenteredFilm[]>([]);
  const [query, setQuery] = useState("");
  const [axis, setAxis] = useState("");
  const [connection, setConnection] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetch("/music_centered_films.csv").then(response => response.text()).then(text => setData(parseCSV(text) as MusicCenteredFilm[]));
  }, []);

  const axes = useMemo(() => [...new Set(data.map(item => item.music_axis).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fa")), [data]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return data.filter(item => {
      const connected = Boolean(item.film_id || item.documentary_id || item.animation_id);
      return (!normalized || `${item.title} ${item.persian_title} ${item.director} ${item.country} ${item.imdb_id} ${item.music_axis}`.toLocaleLowerCase().includes(normalized))
        && (!axis || item.music_axis === axis)
        && (!connection || (connection === "connected" ? connected : !connected));
    });
  }, [data, query, axis, connection]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const linkedFilms = data.filter(item => item.film_id).length;
  const linkedDocuments = data.filter(item => item.documentary_id).length;
  const independent = data.filter(item => !item.film_id && !item.documentary_id && !item.animation_id).length;

  return <main className="films-shell documentaries-shell music-centered-shell" dir="rtl">
    <div className="topbar"><div className="wrap">
      <nav className="nav"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><div className="section-nav"><Link href="/films">فیلم‌ها</Link><Link href="/numbers">شماره‌ها</Link><Link href="/documentaries">مستندها</Link><Link href="/animations">انیمیشن‌ها</Link><Link className="active" href="/music-centered">موسیقی‌محور</Link></div></nav>
      <div className="toolbar music-centered-toolbar">
        <input value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} placeholder="جست‌وجوی عنوان، کارگردان، شناسه یا محور موسیقایی…" aria-label="جست‌وجوی فیلم‌های موسیقی‌محور" />
        <select value={axis} onChange={event => { setAxis(event.target.value); setPage(1); }} aria-label="محور موسیقایی"><option value="">همهٔ محورهای موسیقایی</option>{axes.map(value => <option value={value} key={value}>{value}</option>)}</select>
        <select value={connection} onChange={event => { setConnection(event.target.value); setPage(1); }} aria-label="وضعیت اتصال"><option value="">متصل و مستقل</option><option value="connected">متصل به موجودی درگاه</option><option value="independent">مستقل از موجودی درگاه</option></select>
      </div>
    </div></div>

    {!data.length ? <div className="loading">در حال آماده‌سازی فهرست فیلم‌های موسیقی‌محور…</div> : <div className="wrap list-wrap">
      <header className="directory-heading music-centered-heading"><div><div className="eyebrow">MUS-MC · MUSIC-CENTERED CINEMA</div><h1>فیلم‌های موسیقی‌محور</h1><p>فیلم‌هایی که موزیکال یا شبه‌موزیکال نیستند، اما موسیقی در روایت، شخصیت، اجرا، حافظه یا ساختمان صوری آن‌ها نقش تعیین‌کننده دارد. این فهرست از شمار فیلم‌های موزیکال، مستندها و انیمیشن‌ها کاملاً مستقل است.</p></div><a className="button secondary" href="/downloads/music_centered_films.csv" download>دریافت CSV ↓</a></header>
      <div className="music-centered-stats" aria-label="آمار اتصال‌ها"><span><b>{data.length.toLocaleString("fa-IR")}</b> عنوان منتخب</span><span><b>{linkedFilms.toLocaleString("fa-IR")}</b> اتصال به فیلم موجود</span><span><b>{linkedDocuments.toLocaleString("fa-IR")}</b> اتصال به مستند موجود</span><span><b>{independent.toLocaleString("fa-IR")}</b> رکورد مستقل</span></div>
      <div className="summary">نمایش {filtered.length.toLocaleString("fa-IR")} عنوان از {data.length.toLocaleString("fa-IR")} فیلم موسیقی‌محور</div>
      <div className="film-grid">{shown.map(item => <article className="film-card documentary-card music-centered-card" key={item.music_centered_id}>
        <div className="record-id">{item.music_centered_id}</div>
        <div className="film-title-fa">{item.persian_title}</div>
        <div className="film-title" dir="ltr">{item.title}</div>
        <div className="film-meta">{[item.year, item.country, item.imdb_id].filter(Boolean).join(" · ")}</div>
        <div className="documentary-badges"><span>{item.music_axis}</span>{item.film_id && <span>متصل به فیلم</span>}{item.documentary_id && <span>متصل به مستند</span>}{!item.film_id && !item.documentary_id && !item.animation_id && <span className="independent-badge">مستقل</span>}</div>
        <div className="film-row"><span className="film-label">کارگردان: </span><span dir="ltr">{item.director}</span></div>
        <div className="card-actions">
          {item.film_id && <Link className="details-button" href={`/films?film_id=${encodeURIComponent(item.film_id)}`}>پروندهٔ فیلم موجود</Link>}
          {!item.film_id && item.documentary_id && <Link className="details-button" href={`/documentary?id=${encodeURIComponent(item.documentary_id)}`}>پروندهٔ مستند موجود</Link>}
          <a className="external-link imdb" href={item.imdb_url} target="_blank" rel="noreferrer">IMDb ↗</a>
          {item.thirtynama_url && <a className="modal-link thirtynama compact-link" href={item.thirtynama_url} target="_blank" rel="noreferrer">۳۰نما ↗</a>}
          <a className="downloadroz-button" href={item.downloadroz_search_url} target="_blank" rel="noreferrer">دانلودروز ↗</a>
          <GPTButton prompt={prompt(item)} />
        </div>
      </article>)}</div>
      <div className="pagination"><button className="page-button" disabled={page === 1} onClick={() => { setPage(value => value - 1); scrollTo(0, 0); }}>قبلی</button><span>صفحهٔ {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}</span><button className="page-button" disabled={page === pages} onClick={() => { setPage(value => value + 1); scrollTo(0, 0); }}>بعدی</button></div>
    </div>}
  </main>;
}
