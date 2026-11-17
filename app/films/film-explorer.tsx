"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import GPTButton from "../gpt-button";
import "./genre-chips.css";

type Film=Record<string,string>&{title:string;persian_title:string;year:string;director:string;country:string;genre_1:string;genre_2:string;format:string;style_1:string;style_2:string;actors:string;composer:string;lyricist:string;letterboxd_url:string;imdb_url:string;imdb_music:string;imdb_musical:string;wikipedia_url:string;spotify_uri:string;online_availability:string;thirtynama_url:string;downloadroz_search_url:string};
type FormatRow={film_id:string;format:string};
type GenreRow={film_id:string;genre_1:string;genre_2:string};
type StyleRow={film_id:string;style_1:string;style_2:string};
type NumberRow={number_id:string;film_id:string;number_title:string;youtube_url:string};
type FilmYouTube={film_id:string;youtube_film_url:string;youtube_film_label:string;verification_note:string};
const PAGE=36;
const BASE_PATH=process.env.NEXT_PUBLIC_BASE_PATH||"";
const roles:Record<string,string>={director:"کارگردان‌ها",actors:"بازیگران",composer:"آهنگسازان",lyricist:"ترانه‌سرایان",music_director:"مدیران موسیقی",arranger:"تنظیم‌کنندگان",orchestrator:"ارکستراتورها",vocal_arranger:"تنظیم‌کنندگان آواز",dance_arranger:"تنظیم‌کنندگان رقص",conductor:"رهبران ارکستر",musical_supervisor:"سرپرستان موسیقی",choreographer:"طراحان رقص"};
const details:[string,string][]=[["genre_1","ژانر اصلی"],["genre_2","ژانرهای تکمیلی"],["style_1","سبک موسیقایی اصلی"],["style_2","سبک موسیقایی دوم"],["format","قالب"],["collection","بخش / مجموعه"],["director","کارگردان"],["actors","بازیگران"],["composer","آهنگساز"],["lyricist","ترانه‌سرا"],["music_director","مدیر موسیقی"],["arranger","تنظیم‌کننده"],["orchestrator","ارکستراتور"],["vocal_arranger","تنظیم‌کنندهٔ آواز"],["dance_arranger","تنظیم‌کنندهٔ رقص"],["conductor","رهبر ارکستر"],["musical_supervisor","سرپرست موسیقی"],["choreographer","طراح رقص"]];
const personFields=new Set(details.map(([key])=>key).filter(key=>!["genre_1","genre_2","style_1","style_2","format","collection"].includes(key)));
function names(value:string){return value.split(/\s*[;؛]\s*|\s+،\s+/).map(v=>v.trim()).filter(Boolean)}
function PersonLinks({value,role}:{value:string;role:string}){return <>{names(value).map((name,i)=><span key={`${name}-${i}`}>{i>0&&<span>؛ </span>}<Link className="person-link" href={`/person?name=${encodeURIComponent(name)}&role=${encodeURIComponent(role)}`}>{name}</Link></span>)}</>}
function ImdbGenreTags({film}:{film:Film}){return <>{(film.imdb_music==="1"||film.imdb_musical==="1")&&<div className="imdb-genre-tags" aria-label="برچسب‌های رسمی IMDb">{film.imdb_music==="1"&&<a className="imdb-genre-chip music" href="/films?imdb_tag=music">موسیقی (IMDb)</a>}{film.imdb_musical==="1"&&<a className="imdb-genre-chip musical" href="/films?imdb_tag=musical">موزیکال (IMDb)</a>}</div>}</>}
function filmPrompt(f:Film){return `براساس نظریهٔ علیرضا کاوه این فیلم را دسته‌بندی و تحلیل کن.

لطفاً ژانر، سنت/سبک، جایگاه در تاریخ موزیکال، نسبت با سینمای کلاسیک/مدرن، نقش موسیقی و شماره‌های موزیکال در روایت، اهمیت همکاری عوامل و چند کلیدواژهٔ پژوهشی را پیشنهاد بده. پاسخ فارسی، تحلیلی و روشن باشد و اگر داده‌ای قطعی نیست آن را حدس نزن.

Title: ${f.title||"—"}
Persian title: ${f.persian_title||"—"}
Year: ${f.year||"—"}
Director: ${f.director||"—"}
Actors: ${f.actors||"—"}
Composer: ${f.composer||"—"}
Lyricist: ${f.lyricist||"—"}
Country: ${f.country||"—"}
Primary genre: ${f.genre_1||"—"}
Secondary genre: ${f.genre_2||"—"}
Format: ${f.format||"—"}
Musical style: ${[f.style_1,f.style_2].filter(Boolean).join("؛ ")||"—"}
Collection: ${f.collection||"—"}`}

function parseCSV(text:string):Film[]{
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}
  if(cell||row.length){row.push(cell);rows.push(row)}
  const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];
  return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])) as unknown as Film);
}

export default function FilmExplorer({genrePage=false,stylePage=false}:{genrePage?:boolean;stylePage?:boolean}){
  const [data,setData]=useState<Film[]>([]),[numbers,setNumbers]=useState<NumberRow[]>([]),[filmYouTube,setFilmYouTube]=useState<FilmYouTube[]>([]),[query,setQuery]=useState(""),[year,setYear]=useState(""),[country,setCountry]=useState(""),[genre,setGenre]=useState(""),[format,setFormat]=useState(""),[style,setStyle]=useState(""),[imdbTag,setImdbTag]=useState(""),[page,setPage]=useState(1),[selected,setSelected]=useState<Film|null>(null);
  useEffect(()=>{if(genrePage)setGenre(new URLSearchParams(window.location.search).get("name")||"")},[genrePage]);
  useEffect(()=>{if(stylePage)setStyle(new URLSearchParams(window.location.search).get("name")||"")},[stylePage]);
  useEffect(()=>{setImdbTag(new URLSearchParams(window.location.search).get("imdb_tag")||"")},[]);
  useEffect(()=>{Promise.all([fetch("/musical_portal_4409.csv").then(r=>r.text()),fetch("/film_formats.csv").then(r=>r.text()),fetch("/film_genres.csv").then(r=>r.text()),fetch("/film_styles.csv").then(r=>r.text())]).then(([filmsText,formatsText,genresText,stylesText])=>{const formats=parseCSV(formatsText) as unknown as FormatRow[];const genres=parseCSV(genresText) as unknown as GenreRow[];const styles=parseCSV(stylesText) as unknown as StyleRow[];const formatByFilm=new Map(formats.map(row=>[row.film_id,row.format]));const genreByFilm=new Map(genres.map(row=>[row.film_id,row]));const styleByFilm=new Map(styles.map(row=>[row.film_id,row]));setData(parseCSV(filmsText).map(film=>({...film,format:formatByFilm.get(film.film_id)||"",genre_1:genreByFilm.get(film.film_id)?.genre_1||"",genre_2:genreByFilm.get(film.film_id)?.genre_2||"",style_1:styleByFilm.get(film.film_id)?.style_1||"",style_2:styleByFilm.get(film.film_id)?.style_2||""})))})},[]);
  useEffect(()=>{fetch("/musical_numbers_572.csv").then(r=>r.text()).then(t=>setNumbers(parseCSV(t) as unknown as NumberRow[]))},[]);
  useEffect(()=>{fetch("/film_youtube_first_50.csv").then(r=>r.text()).then(t=>setFilmYouTube(parseCSV(t) as unknown as FilmYouTube[]))},[]);
  useEffect(()=>{if(!data.length)return;const id=new URLSearchParams(location.search).get("film_id");if(id)setSelected(data.find(f=>f.film_id===id||f.legacy_film_ids?.split(/\s*;\s*/).includes(id))||null)},[data]);
  const years=useMemo(()=>[...new Set(data.map(f=>f.year).filter(Boolean))].sort((a,b)=>+b-+a),[data]);
  const countries=useMemo(()=>[...new Set(data.map(f=>f.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"fa")),[data]);
  const splitTags=(value:string)=>value.split("؛").map(tag=>tag.trim()).filter(Boolean);
  const genres=useMemo(()=>[...new Set(data.flatMap(f=>splitTags(f.genre_2)))].sort((a,b)=>a.localeCompare(b,"fa")),[data]);
  const formats=useMemo(()=>[...new Set(data.flatMap(f=>splitTags(f.format)))].sort((a,b)=>a.localeCompare(b,"fa")),[data]);
  const styles=useMemo(()=>[...new Set(data.flatMap(f=>[f.style_1,f.style_2]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"fa")),[data]);
  const filtered=useMemo(()=>{const q=query.trim().toLocaleLowerCase();return data.filter(f=>(!q||Object.entries(f).filter(([key])=>!["play_url","note_path"].includes(key)).map(([,value])=>value).join(" ").toLocaleLowerCase().includes(q))&&(!year||f.year===year)&&(!country||f.country===country)&&(!genre||splitTags(f.genre_2).includes(genre))&&(!format||splitTags(f.format).includes(format))&&(!style||f.style_1===style||f.style_2===style)&&(!imdbTag||(imdbTag==="music"&&f.imdb_music==="1")||(imdbTag==="musical"&&f.imdb_musical==="1")||(imdbTag==="both"&&f.imdb_music==="1"&&f.imdb_musical==="1")))},[data,query,year,country,genre,format,style,imdbTag]);
  useEffect(()=>setPage(1),[query,year,country,genre,format,style,imdbTag]); const pages=Math.max(1,Math.ceil(filtered.length/PAGE)); const shown=filtered.slice((page-1)*PAGE,page*PAGE);
  return <main className="films-shell" dir="rtl">
    <div className="topbar"><div className="wrap"><nav className="nav"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><Link className="nav-note" href="/">بازگشت به صفحهٔ اصلی</Link></nav><div className="toolbar">
      <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="جست‌وجو در تمام فیلم‌ها و عوامل موزیکال…" aria-label="جست‌وجوی فیلم‌ها و تمام عوامل"/>
      <select value={year} onChange={e=>setYear(e.target.value)} aria-label="سال"><option value="">همهٔ سال‌ها</option>{years.map(y=><option key={y}>{y}</option>)}</select>
      <select value={country} onChange={e=>setCountry(e.target.value)} aria-label="کشور"><option value="">همهٔ کشورها</option>{countries.map(c=><option key={c}>{c}</option>)}</select><select value={genre} onChange={e=>setGenre(e.target.value)} aria-label="ژانر تکمیلی"><option value="">همهٔ ژانرها</option>{genres.map(value=><option key={value}>{value}</option>)}</select><select value={format} onChange={e=>setFormat(e.target.value)} aria-label="قالب"><option value="">همهٔ قالب‌ها</option>{formats.map(value=><option key={value}>{value}</option>)}</select><select value={style} onChange={e=>setStyle(e.target.value)} aria-label="سبک موسیقایی"><option value="">همهٔ سبک‌ها</option>{styles.map(value=><option key={value}>{value}</option>)}</select><select value={imdbTag} onChange={e=>setImdbTag(e.target.value)} aria-label="برچسب رسمی IMDb"><option value="">همهٔ برچسب‌های IMDb</option><option value="music">موسیقی — ۱٬۲۲۶</option><option value="musical">موزیکال — ۲٬۰۷۰</option><option value="both">هر دو — ۶۶</option></select><select defaultValue="" onChange={e=>{if(e.target.value==="musical_numbers")window.location.href=`${BASE_PATH}/numbers`;else if(e.target.value)window.location.href=`${BASE_PATH}/people?role=${encodeURIComponent(e.target.value)}`}} aria-label="تخصص"><option value="">همهٔ تخصص‌ها</option>{Object.entries(roles).map(([key,label])=><option value={key} key={key}>{label}</option>)}<option value="musical_numbers">شماره‌های موزیکال</option></select>
      <button className="style-nav" onClick={()=>window.location.href=`${BASE_PATH}/styles`}>سبک‌های موسیقایی</button>
      <button className="style-nav" onClick={()=>window.location.href=`${BASE_PATH}/documentaries`}>مستندها</button>
      <button className="style-nav" onClick={()=>window.location.href=`${BASE_PATH}/animations`}>انیمیشن‌ها</button>
      <button className="style-nav" onClick={()=>window.location.href=`${BASE_PATH}/music-centered`}>موسیقی‌محور</button>
      <button className="collaboration-nav" onClick={()=>window.location.href=`${BASE_PATH}/collaborations`}>همکاری‌ها</button>
    </div></div></div>
    {!data.length?<div className="loading">در حال آماده‌سازی فهرست…</div>:<div className="wrap list-wrap">{genrePage&&<header className="genre-page-heading"><div className="eyebrow">صفحهٔ ژانر</div><h1>{genre||"همهٔ ژانرها"}</h1><p>فیلم‌های موزیکال ثبت‌شده در این ژانر</p></header>}{stylePage&&<header className="genre-page-heading style-page-heading"><div className="eyebrow">صفحهٔ سبک موسیقایی</div><h1>{style||"همهٔ سبک‌ها"}</h1><p>فیلم‌های موزیکال ثبت‌شده در این سبک</p></header>}<div className="summary">نمایش {filtered.length.toLocaleString("fa-IR")} فیلم از {data.length.toLocaleString("fa-IR")} عنوان</div><div className="film-grid">{shown.map((f,i)=><article className="film-card" key={`${f.title}-${f.year}-${i}`}>
      <div className="film-title-fa">{f.persian_title||"بدون عنوان فارسی"}</div><div className="film-title">{f.title||"بدون عنوان"}</div>
      <ImdbGenreTags film={f}/>
      {(f.genre_1||f.genre_2)&&<div className="film-genres" aria-label="ژانرهای فیلم">{[...splitTags(f.genre_1),...splitTags(f.genre_2)].map(value=><Link className="genre-chip" href={`/genre?name=${encodeURIComponent(value)}`} key={value}>{value}</Link>)}</div>}
      {(f.style_1||f.style_2)&&<div className="film-styles" aria-label="سبک‌های موسیقایی فیلم">{[f.style_1,f.style_2].filter(Boolean).map(value=><Link className="style-chip" href={`/style?name=${encodeURIComponent(value)}`} key={value}>{value}</Link>)}</div>}
      <div className="film-meta">{[f.year,f.country].filter(Boolean).join(" · ")||"اطلاعات سال و کشور ثبت نشده"}</div>
      {f.online_availability&&<div className="availability-badge">● {f.online_availability}</div>}
      {f.director&&<div className="film-row"><span className="film-label">کارگردان: </span><PersonLinks value={f.director} role="director"/></div>}{f.actors&&<div className="film-row"><span className="film-label">بازیگران: </span><PersonLinks value={f.actors} role="actors"/></div>}{f.composer&&<div className="film-row"><span className="film-label">آهنگساز: </span><PersonLinks value={f.composer} role="composer"/></div>}{f.lyricist&&<div className="film-row"><span className="film-label">ترانه‌سرا: </span><PersonLinks value={f.lyricist} role="lyricist"/></div>}
      <div className="card-actions"><button className="details-button" onClick={()=>setSelected(f)}>اطلاعات کامل</button>{f.downloadroz_search_url&&<a className="downloadroz-button" href={f.downloadroz_search_url} target="_blank" rel="noreferrer">جست‌وجو در دانلودروز ↗</a>}<GPTButton prompt={filmPrompt(f)}/>{filmYouTube.find(y=>y.film_id===f.film_id)?.youtube_film_url&&<a className="external-link youtube" href={filmYouTube.find(y=>y.film_id===f.film_id)?.youtube_film_url} title={filmYouTube.find(y=>y.film_id===f.film_id)?.verification_note} target="_blank" rel="noreferrer">{filmYouTube.find(y=>y.film_id===f.film_id)?.youtube_film_label} ↗</a>}{f.letterboxd_url&&<a className="external-link letterboxd" href={f.letterboxd_url} target="_blank" rel="noreferrer">Letterboxd ↗</a>}{f.imdb_url&&<a className="external-link imdb" href={f.imdb_url} target="_blank" rel="noreferrer">IMDb ↗</a>}{f.wikipedia_url&&<a className="external-link wikipedia" href={f.wikipedia_url} target="_blank" rel="noreferrer">Wikipedia ↗</a>}{f.spotify_uri&&<a className="external-link spotify" href={f.spotify_uri} target="_blank" rel="noreferrer">Spotify ↗</a>}</div>
    </article>)}</div><div className="pagination"><button className="page-button" disabled={page===1} onClick={()=>{setPage(p=>p-1);scrollTo(0,0)}}>قبلی</button><span>صفحهٔ {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}</span><button className="page-button" disabled={page===pages} onClick={()=>{setPage(p=>p+1);scrollTo(0,0)}}>بعدی</button></div></div>}
    {selected&&<div className="modal-backdrop" role="presentation" onMouseDown={()=>setSelected(null)}><section className="film-modal" role="dialog" aria-modal="true" aria-label={`اطلاعات کامل ${selected.persian_title||selected.title}`} onMouseDown={e=>e.stopPropagation()}><button className="modal-close" onClick={()=>setSelected(null)} aria-label="بستن">×</button><div className="eyebrow">پروندهٔ کامل فیلم</div><h2>{selected.persian_title}</h2><div className="modal-original-title" dir="ltr">{selected.title}</div><div className="modal-meta">{[selected.year,selected.country].filter(Boolean).join(" · ")}</div><ImdbGenreTags film={selected}/>{selected.online_availability&&<div className="availability-badge modal-availability">● {selected.online_availability}</div>}<GPTButton prompt={filmPrompt(selected)} className="gpt-button-large"/><div className="detail-list">{details.filter(([key])=>selected[key]).map(([key,label])=><div className="detail-item" key={key}><span>{label}</span><p>{personFields.has(key)?<PersonLinks value={selected[key]} role={key}/>:selected[key]}</p></div>)}</div>{numbers.some(n=>n.film_id===selected.film_id)&&<div className="film-numbers"><h3>شماره‌های موزیکال</h3>{numbers.filter(n=>n.film_id===selected.film_id).map(n=><div className="film-number-row" key={n.number_id}><Link href={`/number?id=${encodeURIComponent(n.number_id)}`} dir="ltr">{n.number_title}</Link><a href={n.youtube_url} target="_blank" rel="noreferrer">YouTube ↗</a></div>)}</div>}<div className="modal-actions">{selected.downloadroz_search_url&&<a className="modal-link downloadroz" href={selected.downloadroz_search_url} target="_blank" rel="noreferrer">جست‌وجو در دانلودروز ↗</a>}{selected.thirtynama_url&&<a className="modal-link thirtynama" href={selected.thirtynama_url} target="_blank" rel="noreferrer">مشاهده در ۳۰نما ↗</a>}{selected.letterboxd_url&&<a className="modal-link" href={selected.letterboxd_url} target="_blank" rel="noreferrer">مشاهده در Letterboxd ↗</a>}{selected.imdb_url&&<a className="modal-link imdb" href={selected.imdb_url} target="_blank" rel="noreferrer">مشاهده در IMDb ↗</a>}{selected.wikipedia_url&&<a className="modal-link wikipedia" href={selected.wikipedia_url} target="_blank" rel="noreferrer">مشاهده در Wikipedia ↗</a>}{selected.spotify_uri&&<a className="modal-link spotify" href={selected.spotify_uri} target="_blank" rel="noreferrer">شنیدن آلبوم در Spotify ↗</a>}</div></section></div>}
  </main>
}
