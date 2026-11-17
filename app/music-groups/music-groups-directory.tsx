"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";

type Row=Record<string,string>;
type Group=Row&{group_id:string;imdb_id:string;name:string;identity_type:string;film_count:string;documentary_count:string;confidence:string;imdb_url:string};
type Relation=Row&{group_id:string;work_type:string;work_id:string;title:string;persian_title:string;year:string;role:string};

function parseCSV(text:string):Row[]{
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}
  if(cell||row.length){row.push(cell);rows.push(row)}
  const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];
  return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])));
}

export default function MusicGroupsDirectory(){
  const [groups,setGroups]=useState<Group[]>([]),[relations,setRelations]=useState<Relation[]>([]),[query,setQuery]=useState("");
  useEffect(()=>{Promise.all([fetch("/music_groups.csv").then(r=>r.text()),fetch("/music_group_relations.csv").then(r=>r.text())]).then(([g,r])=>{setGroups(parseCSV(g) as Group[]);setRelations(parseCSV(r) as Relation[])})},[]);
  const examples=useMemo(()=>{const map=new Map<string,string[]>();relations.forEach(r=>map.set(r.group_id,[...(map.get(r.group_id)||[]),r.persian_title||r.title]));return map},[relations]);
  const filtered=useMemo(()=>{const q=query.trim().toLocaleLowerCase();return groups.filter(g=>!q||g.name.toLocaleLowerCase().includes(q)||(examples.get(g.group_id)||[]).join(" ").toLocaleLowerCase().includes(q)).sort((a,b)=>(+b.film_count + +b.documentary_count)-(+a.film_count + +a.documentary_count)||a.name.localeCompare(b.name,"en"))},[groups,examples,query]);
  const filmGroups=groups.filter(g=>+g.film_count>0).length,documentaryGroups=groups.filter(g=>+g.documentary_count>0).length;
  return <main className="music-groups-shell" dir="rtl">
    <nav className="nav wrap"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><Link className="nav-note" href="/films">بازگشت به فهرست فیلم‌ها</Link></nav>
    <section className="music-groups-hero wrap"><div className="eyebrow">MUSIC GROUPS · FILMS</div><h1>گروه‌های موسیقی و فیلم‌ها</h1><p>گروه‌ها و Bandهای واقعی با هویت مستقل موسیقایی؛ در پیوند با فیلم‌هایی که در آن‌ها حضور داشته‌اند و مستندهایی که موضوع یا بخش محوری آن‌ها بوده‌اند.</p><div className="music-groups-summary"><b>{groups.length.toLocaleString("fa-IR")}</b> گروه · <b>{filmGroups.toLocaleString("fa-IR")}</b> گروه در فیلم‌ها · <b>{documentaryGroups.toLocaleString("fa-IR")}</b> گروه در مستندها</div><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="جست‌وجوی نام گروه یا فیلم…" aria-label="جست‌وجوی گروه‌های موسیقی"/></section>
    {!groups.length?<div className="loading">در حال آماده‌سازی گروه‌ها…</div>:<section className="music-groups-grid wrap">{filtered.map(group=><Link className="music-group-card" href={`/music-group?id=${encodeURIComponent(group.group_id)}`} key={group.group_id}><div className="music-group-counts">{+group.film_count>0&&<span>{(+group.film_count).toLocaleString("fa-IR")} فیلم</span>}{+group.documentary_count>0&&<span>{(+group.documentary_count).toLocaleString("fa-IR")} مستند</span>}</div><h2 dir="ltr">{group.name}</h2>{(examples.get(group.group_id)||[]).length>0&&<p>{(examples.get(group.group_id)||[]).slice(0,3).join("، ")}</p>}</Link>)}</section>}
  </main>
}
