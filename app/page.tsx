import Link from "next/link";
import "./exports.css";

export default function Home() {
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
            <Link className="button secondary" href="/numbers">شماره‌های موزیکال</Link>
            <Link className="button secondary" href="/documentaries">مستندها</Link>
            <Link className="button secondary" href="/animations">انیمیشن‌ها</Link>
            <Link className="button secondary" href="/music-centered">فیلم‌های موسیقی‌محور</Link>
            <Link className="button secondary" href="/guide">شیوه‌نامه و تاریخچه</Link>
            <a className="button secondary" href="#exports">خروجی و پشتیبان</a>
            <a className="button secondary" href="#about">دربارهٔ پایگاه</a>
          </div>
          <div className="stats">
            <div className="stat"><b>۴٬۵۷۱</b><span>فیلم یکتای ثبت‌شده</span></div>
            <div className="stat"><b>۷۳۹</b><span>مستند مستقل</span></div>
            <div className="stat"><b>۲۷۴</b><span>انیمیشن مستقل</span></div>
            <div className="stat"><b>۶۰</b><span>فیلم موسیقی‌محور</span></div>
            <div className="stat"><b>۱٬۰۹۵</b><span>شمارهٔ موزیکال</span></div>
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
          <article><div className="export-mark">CSV</div><h3>پایگاه کامل ۴۵۷۱ فیلم یکتا</h3><p>یک فایل یکپارچه شامل گونه، قالب، سبک، عوامل، اتصال‌های بیرونی و سابقهٔ ادغام شناسه‌ها.</p><a className="button" href="/downloads/musical_portal_complete_4571.csv" download>دریافت CSV کامل ↓</a></article>
          <article><div className="export-mark">DOC</div><h3>۷۳۹ مستند</h3><p>همهٔ مستندهای موجود، با صافی مستند موسیقایی و همراه کارگردان، عوامل، دپارتمان موسیقی و شخصیت‌های موضوع.</p><a className="button secondary" href="/downloads/documentaries_all.csv" download>دریافت CSV مستندها ↓</a><div className="minor-downloads"><a href="/downloads/documentary_credits.csv" download>جدول عوامل</a><a href="/downloads/documentary_subjects.csv" download>جدول موضوع‌ها و گروه‌ها</a></div></article>
          <article><div className="export-mark">ANI</div><h3>۲۷۴ انیمیشن</h3><p>فهرست یکتای انیمیشن‌ها با شناسهٔ مستقل، عوامل IMDb، ۲۴ عنوان قطعی بازیابی‌شده و ۴۴ عنوان بلند تازهٔ ۳۰نما.</p><a className="button secondary" href="/downloads/animations_all.csv" download>دریافت CSV انیمیشن‌ها ↓</a><div className="minor-downloads"><a href="/downloads/animation_credits.csv" download>جدول عوامل</a></div></article>
          <article><div className="export-mark">MC</div><h3>۶۰ فیلم موسیقی‌محور</h3><p>فهرست مستقل مدخل کتاب؛ ۲۱ اتصال مستقیم به فیلم‌های موجود و ۳۹ رکورد مستقل، بدون افزایش شمار فیلم‌های موزیکال.</p><a className="button secondary" href="/downloads/music_centered_films.csv" download>دریافت CSV موسیقی‌محورها ↓</a></article>
          <article><div className="export-mark">ZIP</div><h3>پشتیبان کامل و قابل‌انتقال</h3><p>کدها، همهٔ جدول‌ها، خروجی کامل، دفتر ممیزی، تاریخچه و دستور کار بازیابی.</p><a className="button secondary" href="/downloads/musical_portal_backup_v53.zip" download>دریافت پشتیبان ZIP ↓</a></article>
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
