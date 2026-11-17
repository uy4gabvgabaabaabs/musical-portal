"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import GPTButton from "../gpt-button";

type Documentary=Record<string,string>&{
  documentary_id:string;film_id:string;title:string;persian_title:string;year:string;director:string;country:string;
  imdb_id:string;imdb_url:string;imdb_genres:string;imdb_type:string;runtime_minutes:string;imdb_rating:string;
  thirtynama_url:string;downloadroz_search_url:string;source_status:string;selection_basis:string;composer:string;music_department:string;subjects:string;music_subjects:string;documentary_scope:string;
};
const PAGE=36;

function parseCSV(text:string):Documentary[]{
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}
  if(cell||row.length){row.push(cell);rows.push(row)}
  const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];
  return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])) as Documentary);
}

function splitNames(value:string){return value.split(/\s*[;؛]\s*/).map(name=>name.trim()).filter(Boolean)}
function PersonNames({value}:{value:string}){return <span className="inline-person-links">{splitNames(value).map((name,index)=><span key={`${name}-${index}`}>{index>0&&"، "}<Link className="person-link" href={`/person?name=${encodeURIComponent(name)}`} dir="ltr">{name}</Link></span>)}</span>}

function documentaryPrompt(item:Documentary){return `این مستند را برای درگاه موزیکال علیرضا کاوه تحلیل کن. موضوع اصلی، نسبت احتمالی آن با موسیقی و سینما، اهمیت تاریخی و کلیدواژه‌های پژوهشی را به فارسی پیشنهاد بده. اگر داده‌ای قطعی نیست، حدس نزن.\n\nTitle: ${item.title}\nYear: ${item.year}\nDirector: ${item.director||"—"}\nCountry: ${item.country||"—"}\nIMDb genres: ${item.imdb_genres}\nIMDb ID: ${item.imdb_id}`}

export default function DocumentariesDirectory(){
  const [data,setData]=useState<Documentary[]>([]),[query,setQuery]=useState(""),[year,setYear]=useState(""),[type,setType]=useState(""),[scope,setScope]=useState(""),[source,setSource]=useState(""),[page,setPage]=useState(1);
  useEffect(()=>{fetch("/documentaries.csv").then(r=>r.text()).then(t=>setData(parseCSV(t)))},[]);
  const years=useMemo(()=>[...new Set(data.map(d=>d.year).filter(Boolean))].sort((a,b)=>+b-+a),[data]);
  const filtered=useMemo(()=>{const q=query.trim().toLocaleLowerCase();return data.filter(d=>(!q||`${d.title} ${d.persian_title} ${d.director} ${d.composer} ${d.music_department} ${d.subjects||d.music_subjects} ${d.country} ${d.imdb_id} ${d.imdb_genres}`.toLocaleLowerCase().includes(q))&&(!year||d.year===year)&&(!type||d.imdb_type===type)&&(!scope||d.documentary_scope===scope)&&(!source||d.source_status===source))},[data,query,year,type,scope,source]);
  const pages=Math.max(1,Math.ceil(filtered.length/PAGE)),shown=filtered.slice((page-1)*PAGE,page*PAGE);
  return <main className="films-shell documentaries-shell" dir="rtl">
    <div className="topbar"><div className="wrap"><nav className="nav"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><div className="section-nav"><Link href="/films">فیلم‌ها</Link><Link href="/numbers">شماره‌ها</Link><Link className="active" href="/documentaries">مستندها</Link><Link href="/animations">انیمیشن‌ها</Link><Link href="/music-centered">موسیقی‌محور</Link></div></nav><div className="toolbar documentaries-toolbar">
      <input value={query} onChange={e=>{setQuery(e.target.value);setPage(1)}} placeholder="جست‌وجوی عنوان، کارگردان یا شناسهٔ IMDb…" aria-label="جست‌وجوی مستندها"/>
      <select value={year} onChange={e=>{setYear(e.target.value);setPage(1)}} aria-label="سال"><option value="">همهٔ سال‌ها</option>{years.map(value=><option key={value}>{value}</option>)}</select>
      <select value={type} onChange={e=>{setType(e.target.value);setPage(1)}} aria-label="نوع"><option value="">فیلم و تلویزیون</option><option value="movie">فیلم سینمایی</option><option value="tvMovie">فیلم تلویزیونی</option></select>
      <select value={scope} onChange={e=>{setScope(e.target.value);setPage(1)}} aria-label="دامنهٔ مستند"><option value="">همهٔ مستندها</option><option value="مستند موسیقایی">مستندهای موسیقایی</option><option value="مستند عمومی">سایر مستندها</option></select>
      <select value={source} onChange={e=>{setSource(e.target.value);setPage(1)}} aria-label="منشأ"><option value="">همهٔ منشأها</option><option value="متصل به فیلم موجود">موجود در درگاه</option><option value="افزوده‌شده از برچسب موسیقی ۳۰نما">افزودهٔ تازه</option></select>
    </div></div></div>
    {!data.length?<div className="loading">در حال آماده‌سازی فهرست مستندها…</div>:<div className="wrap list-wrap">
      <header className="directory-heading"><div><div className="eyebrow">MUS-D · DOCUMENTARIES</div><h1>مستندها</h1><p>فهرست مستقل همهٔ مستندهای شناخته‌شدهٔ درگاه؛ مستندهای موسیقایی با صافی جدا در دسترس‌اند و انیمیشن و ضبط صرفِ کنسرت/تور وارد نشده‌اند.</p></div><a className="button secondary" href="/downloads/documentaries_all.csv" download>دریافت CSV ↓</a></header>
      <div className="summary">نمایش {filtered.length.toLocaleString("fa-IR")} مستند از {data.length.toLocaleString("fa-IR")} عنوان</div>
      <div className="film-grid">{shown.map(item=><article className="film-card documentary-card" key={item.documentary_id}>
        <div className="record-id">{item.documentary_id}</div>{item.persian_title&&<div className="film-title-fa">{item.persian_title}</div>}<div className="film-title">{item.title}</div>
        <div className="film-meta">{[item.year,item.country,item.runtime_minutes&&`${item.runtime_minutes} دقیقه`].filter(Boolean).join(" · ")}</div>
        <div className="documentary-badges"><span>{item.documentary_scope||"مستند"}</span>{item.imdb_type==="tvMovie"&&<span>تلویزیونی</span>}{item.film_id&&<span>متصل به فیلم</span>}</div>
        {item.director&&<div className="film-row"><span className="film-label">کارگردان: </span><PersonNames value={item.director}/></div>}
        {item.composer&&<div className="film-row"><span className="film-label">آهنگ‌ساز: </span><PersonNames value={item.composer}/></div>}
        {(item.subjects||item.music_subjects)&&<div className="film-row subject-line"><span className="film-label">موضوع/شخصیت: </span><PersonNames value={item.subjects||item.music_subjects}/></div>}
        <div className="card-actions"><Link className="details-button" href={`/documentary?id=${encodeURIComponent(item.documentary_id)}`}>پروندهٔ مستند</Link><a className="external-link imdb" href={item.imdb_url} target="_blank" rel="noreferrer">IMDb ↗</a>{item.thirtynama_url&&<a className="modal-link thirtynama compact-link" href={item.thirtynama_url} target="_blank" rel="noreferrer">۳۰نما ↗</a>}<a className="downloadroz-button" href={item.downloadroz_search_url} target="_blank" rel="noreferrer">دانلودروز ↗</a><GPTButton prompt={documentaryPrompt(item)}/></div>
      </article>)}</div>
      <div className="pagination"><button className="page-button" disabled={page===1} onClick={()=>{setPage(p=>p-1);scrollTo(0,0)}}>قبلی</button><span>صفحهٔ {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}</span><button className="page-button" disabled={page===pages} onClick={()=>{setPage(p=>p+1);scrollTo(0,0)}}>بعدی</button></div>
    </div>}
  </main>;
}
