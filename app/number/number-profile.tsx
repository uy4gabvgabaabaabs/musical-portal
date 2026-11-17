"use client";
import Link from "next/link";
import {useEffect,useState} from "react";

type NumberRow=Record<string,string>&{number_id:string;film_id:string;number_title:string;film_title:string;year:string;youtube_url:string};
function parseCSV(text:string):NumberRow[]{
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}
  if(cell||row.length){row.push(cell);rows.push(row)}const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])) as NumberRow);
}
export default function NumberProfile(){
  const [item,setItem]=useState<NumberRow|null|undefined>(undefined);
  useEffect(()=>{const id=new URLSearchParams(location.search).get("id")||"";fetch("/musical_numbers_572.csv").then(r=>r.text()).then(t=>setItem(parseCSV(t).find(n=>n.number_id===id)||null))},[]);
  if(item===undefined)return <main className="profile-shell" dir="rtl"><div className="loading">در حال آماده‌سازی صفحهٔ شماره…</div></main>;
  if(item===null)return <main className="profile-shell" dir="rtl"><section className="profile-card"><h1>شماره پیدا نشد</h1><Link className="details-button" href="/numbers">بازگشت به شماره‌ها</Link></section></main>;
  return <main className="profile-shell" dir="rtl"><section className="profile-card number-profile"><div className="eyebrow">شمارهٔ موزیکال</div><h1 dir="ltr">{item.number_title}</h1><p className="profile-subtitle" dir="ltr">{item.film_title} · {item.year}</p><div className="profile-actions"><a className="modal-link youtube" href={item.youtube_url} target="_blank" rel="noreferrer">{item.youtube_url.includes("/results?")?"جست‌وجوی شماره در YouTube":"تماشا در YouTube"} ↗</a><Link className="modal-link" href={`/films?film_id=${encodeURIComponent(item.film_id)}`}>رفتن به فیلم</Link><Link className="modal-link quiet" href="/numbers">همهٔ شماره‌ها</Link></div></section></main>
}
