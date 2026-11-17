# پشتیبان درگاه موزیکال — نسخهٔ 53

این بسته شامل کدهای سایت، داده‌های پژوهشی، خروجی کامل 4571 فیلم و فهرست‌های مستقل همهٔ مستندها، انیمیشن‌ها و فیلم‌های موسیقی‌محور است.

## فایل‌های داده

- `public/musical_portal_4409.csv`: جدول اصلی فیلم‌ها (نام پایدار قدیمی)
- `public/documentaries.csv`: جدول مستقل همهٔ مستندها با شناسهٔ `MUS-D`
- `public/documentary_credits.csv`: عوامل و دپارتمان موسیقی مستندها
- `public/documentary_subjects.csv`: شخصیت‌ها، گروه‌ها و Bandهای موضوع مستند
- `public/documentaries_excluded_concert_tour.csv`: موارد کنسرت/تور کنارگذاشته‌شده از این مسیر
- `public/animations.csv`: جدول مستقل انیمیشن‌ها با شناسهٔ `MUS-A`
- `public/animation_credits.csv`: کارگردان، آهنگ‌ساز، صداپیشه و عوامل اصلی انیمیشن‌ها
- `public/music_centered_films.csv`: ۶۰ فیلم موسیقی‌محور با شناسهٔ `MUS-MC` و اتصال IMDb به موجودی‌های اصلی
- `public/imdb_music_labels_report.json`: گزارش تطبیق رسمی `Music` و `Musical` در IMDb
- `public/music_groups.csv`: هویت‌های قطعی گروه و Band موسیقی
- `public/music_group_relations.csv`: اتصال گروه‌ها به فیلم‌ها و مستندها
- `public/merge_audit/`: دفتر کامل ادغام بی‌اتلاف IMDb و بازنویسی اتصال‌ها
- `public/music_department_relations_3516.csv`: اتصال کامل فیلم، شخص و سمت موسیقی
- `public/film_genres.csv`: گونه‌ها
- `public/film_formats.csv`: قالب‌ها
- `public/film_styles.csv`: سبک‌های موسیقایی
- `public/musical_numbers_572.csv`: شماره‌های موزیکال (نام پایدار قدیمی)
- `exports/musical_portal_complete_4571.csv`: خروجی یکپارچه
- `exports/documentaries_all.csv`: خروجی مستقل همهٔ مستندها
- `exports/documentary_credits.csv`: خروجی عوامل مستندها
- `exports/documentary_subjects.csv`: خروجی موضوع‌ها و Bandها
- `exports/animations_all.csv`: خروجی مستقل همهٔ انیمیشن‌ها
- `exports/animation_credits.csv`: خروجی عوامل انیمیشن‌ها
- `exports/music_centered_films.csv`: خروجی مستقل فیلم‌های موسیقی‌محور

## حافظه و دستور کار

- `public/docs/musical-portal-guide.md`: شیوه‌نامه و وضعیت جاری
- `public/docs/musical-portal-history.md`: تاریخچهٔ اجرایی نسخه‌به‌نسخه
- `public/docs/musical-portal-operations.md`: دستور کار ادامه، اعتبارسنجی و بازیابی

برای انتقال داده‌ها، فایل پوشهٔ `exports` کافی است. برای اجرای دوبارهٔ سایت، Node.js 22 یا جدیدتر، `npm ci` و سپس `npm run build` لازم است. برای ساخت یک نسخهٔ مستقل روی میزبان دیگر، تنظیمات `.openai/hosting.json` باید با مقصد تازه جایگزین شود.
