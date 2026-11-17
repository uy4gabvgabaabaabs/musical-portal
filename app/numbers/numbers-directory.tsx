"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";

type NumberRow={number_id:string;film_id:string;number_title:string;film_title:string;year:string;youtube_url:string};
const PAGE=40;

function parseCSV(text:string):NumberRow[]{
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}
  if(cell||row.length){row.push(cell);rows.push(row)}
  const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];
  return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])) as unknown as NumberRow);
}

export default function NumbersDirectory(){
  const [data,setData]=useState<NumberRow[]>([]),[query,setQuery]=useState(""),[page,setPage]=useState(1);
  useEffect(()=>{fetch("/musical_numbers_572.csv").then(r=>r.text()).then(t=>setData(parseCSV(t)))},[]);
  const filtered=useMemo(()=>{const q=query.trim().toLocaleLowerCase();return data.filter(n=>!q||`${n.number_title} ${n.film_title} ${n.year}`.toLocaleLowerCase().includes(q))},[data,query]);
  useEffect(()=>setPage(1),[query]);const pages=Math.max(1,Math.ceil(filtered.length/PAGE));const shown=filtered.slice((page-1)*PAGE,page*PAGE);
  return <main className="films-shell numbers-shell" dir="rtl">
    <div className="topbar"><div className="wrap"><nav className="nav"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><Link className="nav-note" href="/films">همهٔ فیلم‌ها</Link></nav><div className="toolbar numbers-toolbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="جست‌وجوی شماره، فیلم یا سال…" aria-label="جست‌وجوی شماره‌های موزیکال"/></div></div></div>
    {!data.length?<div className="loading">در حال آماده‌سازی شماره‌ها…</div>:<div className="wrap list-wrap"><div className="summary">نمایش {filtered.length.toLocaleString("fa-IR")} شماره از {data.length.toLocaleString("fa-IR")} عنوان</div><div className="number-grid">{shown.map(n=><article className="number-card" key={n.number_id}><div className="number-title" dir="ltr">{n.number_title}</div><div className="film-meta" dir="ltr">{n.film_title} · {n.year}</div><div className="card-actions"><Link className="details-button" href={`/number?id=${encodeURIComponent(n.number_id)}`}>صفحهٔ شماره</Link><a className="external-link youtube" href={n.youtube_url} target="_blank" rel="noreferrer">{n.youtube_url.includes("/results?")?"جست‌وجو در YouTube":"پخش در YouTube"} ↗</a></div></article>)}</div><div className="pagination"><button className="page-button" disabled={page===1} onClick={()=>{setPage(p=>p-1);scrollTo(0,0)}}>قبلی</button><span>صفحهٔ {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}</span><button className="page-button" disabled={page===pages} onClick={()=>{setPage(p=>p+1);scrollTo(0,0)}}>بعدی</button></div></div>}
  </main>
}
