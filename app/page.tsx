"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import "./exports.css";

type Counts = { films: number; documentaries: number; animations: number; musicCentered: number; numbers: number };
const initialCounts: Counts = { films: 0, documentaries: 0, animations: 0, musicCentered: 0, numbers: 0 };

function countCsvRecords(text: string) {
  let records = 0, quoted = false, hasContent = false;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (char === '"') {
      if (quoted && text[index + 1] === '"') index++;
      else quoted = !quoted;
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[index + 1] === "\n") index++;
      if (hasContent) records++;
      hasContent = false;
    } else if (!/\s/.test(char)) hasContent = true;
  }
  if (hasContent) records++;
  return Math.max(0, records - 1);
}

const fa = (value: number) => value ? value.toLocaleString("fa-IR") : "…";

export default function Home() {
  const [counts, setCounts] = useState(initialCounts);
  useEffect(() => {
    const sources: [keyof Counts, string][] = [
      ["films", "/musical_portal_4409.csv"],
      ["documentaries", "/documentaries.csv"],
      ["animations", "/animations.csv"],
      ["musicCentered", "/music_centered_films.csv"],
      ["numbers", "/musical_numbers_572.csv"],
    ];
    Promise.all(sources.map(async ([key, url]) => [key, countCsvRecords(await fetch(url).then(response => response.text()))] as const))
      .then(entries => setCounts(Object.fromEntries(entries) as Counts));
  }, []);
  return (
    <main className="home-shell" dir="rtl">
      <nav className="nav wrap">
        <div className="brand">درگاه <span>موزیکال</span></div>
        <div className="nav-note">پایگاه پژوهشی سینمای موزیکال</div>
      </nav>

      <section className="hero wrap">
        <div className="hero-copy">
          <div className="eyebrow">MUSICAL CINEMA PORTAL</div>
          <h1>نقشه‌ای برای ورود به جهان موزیکال</h1>
          <p className="lead">پایگاهی برای مرور فیلم‌ها، بازیگران، آهنگسازان، ترانه‌سرایان و گروه‌های موسیقی؛ از هالیوود کلاسیک تا بالیوود و سینمای معاصر.</p>
          <div className="actions">
            <Link className="button" href="/films">مشاهدهٔ فهرست کامل ←</Link>
            <Link className="button secondary" href="/styles">سبک‌های موسیقایی</Link>
            <Link className="button secondary" href="/music-groups">گروه‌های موسیقی و فیلم‌ها</Link>
            <Link className="button secondary" href="/numbers">شماره‌های موزیکال</Link>
            <Link className="button secondary" href="/documentaries">مستندها</Link>
            <Link className="button secondary" href="/animations">انیمیشن‌ها</Link>
            <Link className="button secondary" href="/music-centered">فیلم‌های موسیقی‌محور</Link>
            <Link className="button secondary" href="/films?scope=global">موزیکال جهانی</Link>
            <Link className="button secondary" href="/guide">شیوه‌نامه و تاریخچه</Link>
            <a className="button secondary" href="#exports">خروجی و پشتیبان</a>
            <a className="button secondary" href="#about">دربارهٔ پایگاه</a>
          </div>
          <div className="stats">
            <div className="stat"><b>{fa(counts.films)}</b><span>فیلم یکتای ثبت‌شده</span></div>
            <div className="stat"><b>{fa(counts.documentaries)}</b><span>مستند مستقل</span></div>
            <div className="stat"><b>{fa(counts.animations)}</b><span>انیمیشن مستقل</span></div>
            <div className="stat"><b>{fa(counts.musicCentered)}</b><span>فیلم موسیقی‌محور</span></div>
            <div className="stat"><b>{fa(counts.numbers)}</b><span>شمارهٔ موزیکال</span></div>
          </div>
        </div>
        <div className="portal-art" aria-label="تصویری انتزاعی از حلقه‌های فیلم و موسیقی">
          <div className="record record-one"/><div className="record record-two"/>
          <div className="art-note"><h2>از فیلم به آدم‌ها؛<br/>از آدم‌ها به فیلم‌ها</h2><p>نسخهٔ نخست فیلم‌محور است؛ پایه‌ای برای ساخت صفحه‌های مستقل اشخاص و پیوندهای میان آن‌ها.</p></div>
        </div>
      </section>

      <section id="exports" className="exports wrap">
        <div className="eyebrow">PORTABLE DATA</div>
        <div className="exports-head"><div><h2>خروجی و پشتیبان درگاه</h2><p>داده‌های کامل را برای Codex، Excel و پایگاه‌های دیگر دریافت کنید، یا نسخهٔ قابل‌انتقال کل درگاه را نگه دارید.</p></div><span>نسخهٔ ۵۳</span></div>
        <div className="export-grid">
          <article><div className="export-mark">CSV</div><h3>پایگاه کامل {fa(counts.films)} فیلم یکتا</h3><p>یک فایل یکپارچه شامل گونه، قالب، سبک، عوامل، اتصال‌های بیرونی و سابقهٔ ادغام شناسه‌ها.</p><a className="button" href="/downloads/musical_portal_complete.csv" download>دریافت CSV کامل ↓</a></article>
          <article><div className="export-mark">DOC</div><h3>{fa(counts.documentaries)} مستند</h3><p>همهٔ مستندهای موجود، با صافی مستند موسیقایی و همراه کارگردان، عوامل، دپارتمان موسیقی و شخصیت‌های موضوع.</p><a className="button secondary" href="/downloads/documentaries_all.csv" download>دریافت CSV مستندها ↓</a><div className="minor-downloads"><a href="/downloads/documentary_credits.csv" download>جدول عوامل</a><a href="/downloads/documentary_subjects.csv" download>جدول موضوع‌ها و گروه‌ها</a></div></article>
          <article><div className="export-mark">ANI</div><h3>{fa(counts.animations)} انیمیشن</h3><p>فهرست یکتای انیمیشن‌ها با شناسهٔ مستقل و اتصال به اطلاعات و عوامل IMDb.</p><a className="button secondary" href="/downloads/animations_all.csv" download>دریافت CSV انیمیشن‌ها ↓</a><div className="minor-downloads"><a href="/downloads/animation_credits.csv" download>جدول عوامل</a></div></article>
          <article><div className="export-mark">MC</div><h3>{fa(counts.musicCentered)} فیلم موسیقی‌محور</h3><p>فهرست مستقل مدخل کتاب، بدون افزایش شمار فیلم‌های موزیکال.</p><a className="button secondary" href="/downloads/music_centered_films.csv" download>دریافت CSV موسیقی‌محورها ↓</a></article>
          <article><div className="export-mark">ZIP</div><h3>پشتیبان کامل و قابل‌انتقال</h3><p>کدها، همهٔ جدول‌ها، خروجی کامل، دفتر ممیزی، تاریخچه و دستور کار بازیابی.</p><a className="button secondary" href="https://github.com/uy4gabvgabaabaabs/musical-portal/archive/refs/heads/main.zip">دریافت پشتیبان ZIP ↓</a></article>
        </div>
      </section>

      <section id="about" className="about wrap">
        <div className="eyebrow">نسخهٔ نخست</div>
        <h2>فهرستی برای دیدن، جست‌وجو و کشف ارتباط‌ها</h2>
        <p className="lead">فهرست فیلم‌ها، مستندها، انیمیشن‌ها، فیلم‌های موسیقی‌محور و شماره‌های موزیکال با شناسه‌های پایدار و پیوندهای بیرونی در دسترس‌اند. جست‌وجو و پالایش، این مجموعهٔ بزرگ را به یک ابزار پژوهشی سریع تبدیل می‌کند.</p>
      </section>
      <footer className="wrap">پایگاه دادهٔ گونهٔ موزیکال سینمایی — علیرضا کاوه</footer>
    </main>
  );
}
