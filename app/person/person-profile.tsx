"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import GPTButton from "../gpt-button";

type Film=Record<string,string>;
type Featured=Record<string,string>;
type Documentary=Record<string,string>&{documentary_id:string;title:string;persian_title:string;year:string;country:string;director:string;documentary_scope:string};
type DocumentaryCredit=Record<string,string>&{documentary_id:string;person_imdb_id:string;person_name:string;role:string};
type DocumentarySubject=Record<string,string>&{documentary_id:string;subject_imdb_id:string;subject_name:string;relation:string};
type Animation=Record<string,string>&{animation_id:string;title:string;persian_title:string;year:string;country:string;director:string;imdb_type:string};
type AnimationCredit=Record<string,string>&{animation_id:string;person_imdb_id:string;person_name:string;role:string};
type Collaboration={name:string;films:Film[];roles:Set<string>};
type Network={names:string[];films:Film[]};

const roleLabels:Record<string,string>={director:"کارگردان",actors:"بازیگر",composer:"آهنگساز",lyricist:"ترانه‌سرا",music_director:"مدیر موسیقی",arranger:"تنظیم‌کننده",orchestrator:"ارکستراتور",vocal_arranger:"تنظیم‌کنندهٔ آواز",dance_arranger:"تنظیم‌کنندهٔ رقص",conductor:"رهبر ارکستر",musical_supervisor:"سرپرست موسیقی",choreographer:"طراح رقص"};
const roleKeys=Object.keys(roleLabels);

function parseCSV(text:string):Record<string,string>[] {const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=""}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell=""}else cell+=c}if(cell||row.length){row.push(cell);rows.push(row)}const headers=rows.shift()?.map(h=>h.replace(/^\uFEFF/,""))??[];return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])))}
function names(value:string){return value.split(/\s*[;؛]\s*|\s+،\s+/).map(v=>v.trim()).filter(Boolean)}
function sameName(a:string,b:string){return a.toLocaleLowerCase()===b.toLocaleLowerCase()}
function combinations(items:string[],size:number){const result:string[][]=[];function visit(start:number,picked:string[]){if(picked.length===size){result.push(picked);return}for(let i=start;i<=items.length-(size-picked.length);i++)visit(i+1,[...picked,items[i]])}visit(0,[]);return result}

export default function PersonProfile(){
 const [data,setData]=useState<Film[]>([]),[featuredPeople,setFeaturedPeople]=useState<Featured[]>([]),[documentaries,setDocumentaries]=useState<Documentary[]>([]),[documentaryCredits,setDocumentaryCredits]=useState<DocumentaryCredit[]>([]),[documentarySubjects,setDocumentarySubjects]=useState<DocumentarySubject[]>([]),[animations,setAnimations]=useState<Animation[]>([]),[animationCredits,setAnimationCredits]=useState<AnimationCredit[]>([]),[name,setName]=useState(""),[imdbId,setImdbId]=useState(""),[showNetworks,setShowNetworks]=useState(false);
 useEffect(()=>{const params=new URLSearchParams(window.location.search);Promise.all([fetch("/musical_portal_4409.csv").then(r=>r.text()),fetch("/featured_people.csv").then(r=>r.text()),fetch("/documentaries.csv").then(r=>r.text()),fetch("/documentary_credits.csv").then(r=>r.text()),fetch("/documentary_subjects.csv").then(r=>r.text()),fetch("/animations.csv").then(r=>r.text()),fetch("/animation_credits.csv").then(r=>r.text())]).then(([films,people,docs,credits,subjects,animationItems,animationRelations])=>{setName(params.get("name")||"");setImdbId(params.get("imdb")||"");setData(parseCSV(films));setFeaturedPeople(parseCSV(people));setDocumentaries(parseCSV(docs) as Documentary[]);setDocumentaryCredits(parseCSV(credits) as DocumentaryCredit[]);setDocumentarySubjects(parseCSV(subjects) as DocumentarySubject[]);setAnimations(parseCSV(animationItems) as Animation[]);setAnimationCredits(parseCSV(animationRelations) as AnimationCredit[])})},[]);
 const featured=useMemo(()=>featuredPeople.find(p=>sameName(p.name,name)||Boolean(p.portal_name)&&sameName(p.portal_name,name)),[featuredPeople,name]);
 const appearances=useMemo(()=>data.flatMap(f=>{const roles=roleKeys.filter(key=>names(f[key]||"").some(n=>sameName(n,name)));return roles.length?[{film:f,roles}]:[]}).sort((a,b)=>(+a.film.year||9999)-(+b.film.year||9999)),[data,name]);
 const roles=useMemo(()=>[...new Set(appearances.flatMap(a=>a.roles))],[appearances]);
 const documentaryAppearances=useMemo(()=>{
  const byId=new Map(documentaries.map(documentary=>[documentary.documentary_id,documentary]));
  const matched=(personName:string,personId:string)=>imdbId?personId===imdbId:sameName(personName,name);
  const relations=new Map<string,Set<string>>();
  for(const credit of documentaryCredits)if(matched(credit.person_name,credit.person_imdb_id)){const item=relations.get(credit.documentary_id)||new Set<string>();item.add(credit.role||"عامل");relations.set(credit.documentary_id,item)}
  for(const subject of documentarySubjects)if(matched(subject.subject_name,subject.subject_imdb_id)){const item=relations.get(subject.documentary_id)||new Set<string>();item.add(subject.relation||"موضوع/شخصیت");relations.set(subject.documentary_id,item)}
  return [...relations].flatMap(([documentaryId,relationRoles])=>{const documentary=byId.get(documentaryId);return documentary?[{documentary,roles:[...relationRoles]}]:[]}).sort((a,b)=>(+a.documentary.year||9999)-(+b.documentary.year||9999));
 },[documentaries,documentaryCredits,documentarySubjects,imdbId,name]);
 const documentaryRoles=useMemo(()=>[...new Set(documentaryAppearances.flatMap(appearance=>appearance.roles))],[documentaryAppearances]);
 const animationAppearances=useMemo(()=>{const byId=new Map(animations.map(item=>[item.animation_id,item])),relations=new Map<string,Set<string>>();for(const credit of animationCredits)if(imdbId?credit.person_imdb_id===imdbId:sameName(credit.person_name,name)){const roles=relations.get(credit.animation_id)||new Set<string>();roles.add(credit.role||"عامل");relations.set(credit.animation_id,roles)}return [...relations].flatMap(([id,itemRoles])=>{const animation=byId.get(id);return animation?[{animation,roles:[...itemRoles]}]:[]}).sort((a,b)=>(+a.animation.year||9999)-(+b.animation.year||9999))},[animations,animationCredits,imdbId,name]);
 const animationRoles=useMemo(()=>[...new Set(animationAppearances.flatMap(appearance=>appearance.roles))],[animationAppearances]);
 const resolvedName=useMemo(()=>animationCredits.find(credit=>imdbId&&credit.person_imdb_id===imdbId)?.person_name||documentaryCredits.find(credit=>imdbId&&credit.person_imdb_id===imdbId)?.person_name||documentarySubjects.find(subject=>imdbId&&subject.subject_imdb_id===imdbId)?.subject_name||featured?.name||name,[animationCredits,documentaryCredits,documentarySubjects,featured,imdbId,name]);
 const collaborations=useMemo(()=>{
  const map=new Map<string,Collaboration>();
  for(const {film} of appearances){
   const seen=new Set<string>();
   for(const role of roleKeys)for(const person of names(film[role]||"")){
    if(sameName(person,name)||seen.has(person))continue;
    seen.add(person);const item=map.get(person)||{name:person,films:[],roles:new Set<string>()};item.films.push(film);item.roles.add(role);map.set(person,item);
   }
  }
 return [...map.values()].filter(x=>x.films.length>=2).sort((a,b)=>b.films.length-a.films.length||a.name.localeCompare(b.name,"fa")).slice(0,12);
 },[appearances,name]);
 const networks=useMemo(()=>{
  if(!showNetworks)return [];
  const map=new Map<string,Network>();
  for(const {film} of appearances){
   const people=[...new Set(roleKeys.flatMap(role=>names(film[role]||"")))].filter(person=>!sameName(person,name)).sort((a,b)=>a.localeCompare(b,"en"));
   for(let size=2;size<=Math.min(4,people.length);size++)for(const group of combinations(people,size)){
    const key=group.join("\u0000"),item=map.get(key)||{names:group,films:[]};item.films.push(film);map.set(key,item);
   }
  }
  const frequent=[...map.values()].filter(item=>item.films.length>=3);
  const maximal=frequent.filter(item=>!frequent.some(other=>other.names.length>item.names.length&&item.names.every(person=>other.names.includes(person))));
  return maximal.sort((a,b)=>b.films.length-a.films.length||b.names.length-a.names.length).slice(0,8);
 },[appearances,name,showNetworks]);
 const personPrompt=useMemo(()=>`براساس نظریهٔ علیرضا کاوه جایگاه این شخص را در سینمای موزیکال تحلیل کن.

لطفاً تخصص‌ها، جایگاه تاریخی، سنت‌ها و سبک‌های مرتبط، مهم‌ترین همکاری‌ها، نقش او در تحول موزیکال و چند کلیدواژهٔ پژوهشی را توضیح بده. پاسخ فارسی، تحلیلی و روشن باشد و اگر داده‌ای قطعی نیست آن را حدس نزن.

Name: ${resolvedName}
Roles: ${[...roles.map(r=>roleLabels[r]),...documentaryRoles,...animationRoles].join("، ")||"—"}
Country: ${featured?.country||"—"}
Films in database: ${appearances.length}
Documentaries in database: ${documentaryAppearances.length}
Animations in database: ${animationAppearances.length}
Selected films: ${appearances.slice(0,12).map(a=>`${a.film.title} (${a.film.year})`).join("؛ ")||"—"}
Frequent collaborators: ${collaborations.slice(0,8).map(c=>`${c.name} (${c.films.length} films)`).join("؛ ")||"—"}`,[animationAppearances,animationRoles,appearances,collaborations,documentaryAppearances,documentaryRoles,featured,resolvedName,roles]);
 if(!data.length)return <main className="person-shell loading" dir="rtl">در حال ساخت پروندهٔ شخص…</main>;
 return <main className="person-shell" dir="rtl">
  <nav className="nav wrap"><Link className="brand" href="/">درگاه <span>موزیکال</span></Link><Link className="nav-note" href="/films">بازگشت به فهرست کامل</Link></nav>
  <header className="person-hero wrap"><div className="eyebrow">{featured?"شخص ویژهٔ درگاه":"پروندهٔ شخص"}</div><h1 dir="ltr">{resolvedName}</h1><div className="role-chips">{roles.map(r=><span key={r}>{roleLabels[r]}</span>)}{documentaryRoles.map(role=><span key={`doc-${role}`}>{role}</span>)}{animationRoles.map(role=><span key={`animation-${role}`}>{role}</span>)}</div><div className="person-quick-meta">{featured?.person_id&&<code>{featured.person_id}</code>}{imdbId&&<a href={`https://www.imdb.com/name/${imdbId}/`} target="_blank" rel="noreferrer">{imdbId} ↗</a>}{featured?.country&&<span>{featured.country}</span>}<span>{appearances.length.toLocaleString("fa-IR")} فیلم</span><span>{documentaryAppearances.length.toLocaleString("fa-IR")} مستند</span><span>{animationAppearances.length.toLocaleString("fa-IR")} انیمیشن</span><GPTButton prompt={personPrompt}/></div></header>
  <section className="wrap person-films">
   <div className="person-section-head"><div><div className="eyebrow">داده‌های پایگاه</div><h2>فیلم‌ها</h2></div><span>{appearances.length.toLocaleString("fa-IR")} عنوان</span></div>
   {appearances.length?<div className="person-grid">{appearances.map(({film,roles},i)=><article className="person-film" key={`${film.film_id||film.title}-${i}`}><div className="film-title-fa">{film.persian_title||film.title}</div><div className="film-title">{film.title}</div><div className="film-meta">{[film.year,film.country].filter(Boolean).join(" · ")}</div><div className="role-line">{roles.map(r=>roleLabels[r]).join("، ")}</div><div className="film-row"><span className="film-label">کارگردان: </span>{film.director||"—"}</div><div className="card-actions"><Link className="details-button internal-film-link" href={`/films?film_id=${encodeURIComponent(film.film_id||"")}`}>پروندهٔ فیلم ←</Link></div></article>)}</div>:<div className="empty-person">فیلم مرتبطی با این املای نام پیدا نشد.</div>}
   {documentaryAppearances.length>0&&<section className="person-documentaries"><div className="person-section-head"><div><div className="eyebrow">روابط مستند</div><h2>مستندها</h2></div><span>{documentaryAppearances.length.toLocaleString("fa-IR")} عنوان</span></div><div className="person-grid">{documentaryAppearances.map(({documentary,roles:docRoles})=><article className="person-film" key={documentary.documentary_id}><div className="film-title-fa">{documentary.persian_title||documentary.title}</div><div className="film-title">{documentary.title}</div><div className="film-meta">{[documentary.year,documentary.country,documentary.documentary_scope].filter(Boolean).join(" · ")}</div><div className="role-line">{docRoles.join("، ")}</div><div className="film-row"><span className="film-label">کارگردان: </span>{documentary.director||"—"}</div><div className="card-actions"><Link className="details-button internal-film-link" href={`/documentary?id=${encodeURIComponent(documentary.documentary_id)}`}>پروندهٔ مستند ←</Link></div></article>)}</div></section>}
   {animationAppearances.length>0&&<section className="person-documentaries"><div className="person-section-head"><div><div className="eyebrow">روابط انیمیشن</div><h2>انیمیشن‌ها</h2></div><span>{animationAppearances.length.toLocaleString("fa-IR")} عنوان</span></div><div className="person-grid">{animationAppearances.map(({animation,roles:itemRoles})=><article className="person-film" key={animation.animation_id}><div className="film-title-fa">{animation.persian_title||animation.title}</div><div className="film-title">{animation.title}</div><div className="film-meta">{[animation.year,animation.country,animation.imdb_type==="short"?"کوتاه":"بلند"].filter(Boolean).join(" · ")}</div><div className="role-line">{itemRoles.join("، ")}</div><div className="film-row"><span className="film-label">کارگردان: </span>{animation.director||"—"}</div><div className="card-actions"><Link className="details-button internal-film-link" href={`/animation?id=${encodeURIComponent(animation.animation_id)}`}>پروندهٔ انیمیشن ←</Link></div></article>)}</div></section>}
   {collaborations.length>0&&<details className="person-collaborations"><summary><span>همکاری‌های پرتکرار</span><small>{collaborations.length.toLocaleString("fa-IR")} همکاری مهم در داده‌های درگاه</small></summary><div className="collaborator-list">{collaborations.map(item=><article key={item.name}><div><Link className="person-link" href={`/person?name=${encodeURIComponent(item.name)}`} dir="ltr">{item.name}</Link><small>{[...item.roles].map(r=>roleLabels[r]).join("، ")}</small></div><div className="collab-count">{item.films.length.toLocaleString("fa-IR")} فیلم مشترک</div><div className="collab-films">{item.films.slice(0,3).map(f=><Link key={f.film_id||f.title} href={`/films?film_id=${encodeURIComponent(f.film_id||"")}`}>{f.persian_title||f.title}</Link>)}</div></article>)}</div><Link className="all-collaborations-link" href="/collaborations">جست‌وجوی کامل شبکهٔ همکاری‌ها ←</Link></details>}
   {appearances.length>=3&&<details className="person-collaborations person-networks" onToggle={event=>{if(event.currentTarget.open)setShowNetworks(true)}}><summary><span>شبکه‌های سه‌نفره و بزرگ‌تر</span><small>دست‌کم ۳ فیلم مشترک</small></summary>{!showNetworks?<div className="network-loading">برای محاسبه، این بخش را باز کنید.</div>:networks.length?<div className="network-list">{networks.map((network,i)=><article key={`${network.names.join("-")}-${i}`}><div className="network-people"><Link className="person-link" href={`/person?name=${encodeURIComponent(name)}`} dir="ltr">{featured?.name||name}</Link>{network.names.map(person=><span key={person}> × <Link className="person-link" href={`/person?name=${encodeURIComponent(person)}`} dir="ltr">{person}</Link></span>)}</div><b>{network.films.length.toLocaleString("fa-IR")} فیلم مشترک</b><div className="collab-films">{network.films.slice(0,3).map(f=><Link key={f.film_id||f.title} href={`/films?film_id=${encodeURIComponent(f.film_id||"")}`}>{f.persian_title||f.title}</Link>)}</div></article>)}</div>:<div className="network-loading">در داده‌های فعلی، شبکه‌ای با دست‌کم سه فیلم مشترک پیدا نشد.</div>}</details>}
  </section>
 </main>
}
