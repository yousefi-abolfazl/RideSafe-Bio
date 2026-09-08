# RideSafe-Bio — لاگ روزانه پیشرفت تسک‌ها

> هر تسک با چک‌لیست پلن تعریف و پس از پیاده‌سازی گام‌به‌گام تیک می‌خورد (بند ۱–۲ `rules.md`).
> قالب هر تسک: Goal / Checkpoints / Changes / Result-Validation.
> نشانگرها: ✅ اعتبارسنجی‌شده · ⏳ معلق (تأیید استاد / نسخه استاندارد / سورس قبلی).

**آخرین بازنگری:** 2026-09-08

---

## فاز ۱ — زیرساخت، معماری و مستندسازی

### Task 1.1 — Git init + .gitignore ✅

- **Goal:** مخزن نسخه‌پدیر عملیاتی با پوشش کامل مصنوعات قابل‌چشم‌پوشی پایتون و منابع لایسنس‌دار پروژه.
- **Checkpoints:**
  - [x] `git init` روی شاخه `main`
  - [x] `.gitignore` پایتونی + استثناهای خاص پروژه (`.obsidian/`, `*.pdf` استاندارد)
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `.gitignore` | ایجاد | پاک‌نگه‌داشتن مخزن از venv/cache/PDFهای لایسنس‌دار | ۸۷۱ بایت، ۵ بخش |
- **Result / Validation:** commit `89ad444`؛ `git status` پس از افزودن تمام فایل‌های پروژه: هیچ PDF/venv/obsidian در لیست ردیابی.

### Task 1.2 — Directory Structure ✅

- **Goal:** درخت پوشه مطابق معماری مصوب: `data/`, `docs/` (۴ سند), `src/`, `tests/`, `app.py`.
- **Checkpoints:**
  - [x] ساخت `data/`, `src/`, `tests/`
  - [x] نگارش چهار سند: `project.md`, `roadmap.md`, `rules.md`, `task_log.md`
  - [x] داربست `app.py` (Streamlit حداقلی قابل‌اجرا)
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `docs/project.md` | ایجاد | منشور و نیازمندی‌ها (FR-1..FR-8 + NFR) | ۲۹۹۴ بایت |
  | `docs/roadmap.md` | ایجاد | فازبندی ۵گانه + ریسک‌ها | ۳۳۲۷ بایت |
  | `docs/rules.md` | ایجاد | قوانین کدنویسی/لایسنس/مراجع | — |
  | `docs/task_log.md` | ایجاد | لاگ پیشرفت | همین فایل |
  | `app.py` | ایجاد | نقطه ورود داشبورد | سالم |
  | `src/__init__.py`, `tests/__init__.py`, `data/.gitkeep` | ایجاد | داربست پکیج | import OK |
- **Result / Validation:** `import src` موفق؛ commit `9cabb15`.

### Task 1.3 — venv + requirements.txt ✅

- **Goal:** محیط مجازی ایزوله با پشته مصوب: numpy, scipy, pandas, streamlit, plotly.
- **Checkpoints:**
  - [x] `python3 -m venv .venv` (Python 3.14)
  - [x] `requirements.txt` با حداقل نسخه‌های سازگار + pytest
  - [x] نصب و صحت‌سنجی import
  - [x] تست دود فیلتر Butterworth (پیش‌نیاز فاز ۲)
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `requirements.txt` | ایجاد | تکرارپذیری محیط | ۲۰۴ بایت |
  | `.venv/` | ایجاد (غیرردیابی) | ایزولاسیون وابستگی‌ها | ۶۷۱MB |
- **Result / Validation:** numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, streamlit 1.63.0, plotly 7.0.0 نصب؛ `butter(4, 5.0, 'low', fs=100)` ضرایب سالم برگرداند.

### Smoke Test — اجرای داشبورد ✅

- **Goal:** اثبات اجرای `app.py` روی سرور واقعی.
- **Result / Validation:** `streamlit run app.py --server.port 8599`؛ health endpoint `200 ok`، صفحه اصلی HTTP 200.

### بازسازی قرارداد کاری (بند rules.md) ✅

- **Goal:** ثبت قوانین مصوب کارفرما به‌عنوان مرجع دائمی.
- **Checkpoints:**
  - [x] بازنویسی `rules.md` با ۱۲ بند قرارداد کاری
  - [x] ساخت `docs/decisions.md` (ADR) با backfill تصمیمات فاز صفر
  - [x] افزودن تاریخ بازنگری به هدر همه فایل‌های Markdown
  - [x] تبدیل `task_log.md` به قالب Goal/Checkpoints/Changes/Result
- **Result / Validation:** همه اسناد هم‌راستا با قرارداد؛ commit جاری.

---


## فاز ۲ — پیش‌پردازش سیگنال و تولید داده‌های آزمون استاندارد



### Task 2.1 — فیلتر استاندارد پایین‌گذر Butterworth ۴قطبه، fc = 5 Hz ✅



- **Goal:** پیاده‌سازی ماژول پیش‌پردازش مشترک `src/preprocessing.py` — فیلتر Butterworth تک‌گذره ۴قطبه با فرکانس قطع 5 Hz طبق ISO 17842-1 §I.2.1 / ASTM F2137 — به‌عنوان تنها نقطه پیش‌پردازش مصرف‌شده توسط هر دو موتور استاندارد (ADR-1)، به‌همراه نگاشت ستون‌ها/واحدها/وارونگی محورها (بندهای ۴–۶ قرارداد).

- **Checkpoints (پلن):**

  - [x] T1 — `src/config.py`: مکان مرکزی پارامترهای فیلتر (order=4، fc=5 Hz) با ارجاع استاندارد در کامنت؛ قابل override توسط آرگومان.
  - [x] T2 — `src/preprocessing.py`:
    - `apply_butterworth_lowpass(df, column_mapping, sampling_rate, filter_params) -> pd.DataFrame`
    - تبدیل واحد $m/s^2 \to g$ (ضریب 9.80665) اختیاری و پیکربندی‌پذیر؛ وارونگی محور با ضرب در −1 به‌ازای هر محور.
    - بدون هیچ import از کتابخانه‌های UI (بند ۴ قرارداد).
  - [x] T3 — `tests/test_preprocessing.py`: ۱۴ آزمون قطعی — همه پاس.
  - [x] T4 — به‌روزرسانی Result در همین لاگ + commit `feat: ...`.


- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `src/config.py` | ایجاد — `FILTER_DEFAULTS` (order=4، cutoff=5، zero_phase=False)، `MS2_TO_G`، نام ستون‌های کانونی | بند ۶: عدم هاردکد آستانه‌ها | ۸۰۹ بایت |
  | `src/preprocessing.py` | ایجاد — `apply_butterworth_lowpass` (SOS + sosfilt پیش‌فرض، sosfiltfilt اختیاری)، `standardize_signal_frame` (نگاشت/واحد/وارونگی/زمان مصنوعی + متادیتا) | تسک ۲.۱ + سه تصمیم کارفرما | ۶.۶KB |
  | `tests/test_preprocessing.py` | ایجاد — ۱۴ آزمون واحد | بند ۷: V&V پیش از اتصال به داشبورد | همه پاس |
  | `docs/decisions.md` | ADR-7 ثبت شد | الزام تصمیم ۱ کارفرما (single-pass + SOS) | ✅ |
- **Result / Validation:** ۱۴/۱۴ آزمون pytest پاس (شامل پایداری، پاسخ پله با بهره DC=1، میرایی 50Hz، عبور 0.5Hz، تشخیص zero_phase، خطاهای fs/Nyquist/نگاشت، تبدیل واحد، وارونگی، زمان مصنوعی و خطای «نه زمان نه fs»). بررسی خودکار: هیچ import ابزار UI در `src/` نیست (بند ۴). Smoke پایپ‌لاین واقعی standardize → filter موفق. دو باگ حین توسعه رفع شد: پاس‌دادن اشتباه "butter" به btype و عدم پشتیبانی نگاشت جزئی/خالی در فیلتر.


### Task 2.2 — اسکریپت شبیه‌ساز داده شتاب `src/synthetic_gen.py` ⏳ (پلن در انتظار تأیید)



- **Goal:** ماژول تولید سیگنال شتاب سنتتیک با چهار شکل‌موج پایه (سینوسی، ذوزنقه‌ای، اسپایک گذرا، نویز گاوسی) — پارامترپذیر، قطعی (seed) و UI-free — به‌عنوان پیش‌نیاز تولید ۴ دیتاست مرزی تسک ۲.۳ و آزمون رگرسیون موتورهای فاز ۳/۵.

- **Checkpoints (پلن):**

  - [ ] T1 — API توابع خالص، همگی با قرارداد یکسان `(fs, duration, seed) -> pd.DataFrame` خروجی `time,ax,ay,az`:

    - `generate_sine_wave(fs, duration, amplitude, frequency, axis="az")`

    - `generate_trapezoid_pulse(fs, duration, plateau_amplitude, ramp_rate_g_per_s, ...)`

    - `generate_transient_spike(fs, duration, peak_amplitude, spike_width_s, ...)`

    - `add_gaussian_noise(df, noise_std_g, seed)`

    - `generate_composite_signal(fs, duration, components, seed)` — ترکیب منبع‌ها (برای سناریوهای ۲.۳)

  - [ ] T2 — بازسازی پالس ذوزنقه‌ای از رئوس پاکت B.5 (خیز/پلاتو/افت) با `plateau_amplitude / ramp_rate` به‌عنوان پارامتر — نه آستانه هاردکد (بند ۶).

  - [ ] T3 — `tests/test_synthetic_gen.py`: آزمون قطعی هر شکل‌موج — دامنه/فرکانس/نرخ بازسازی‌شده، طول سیگنال، قطعیت seed، رعایت پاکت ذوزنقه‌ای، UI-free بودن.

  - [ ] T4 — ثبت Changes/Result در لاگ + commit `feat: ...` + پوش خودکار (بند ۱۰).

- **Changes:** (پس از پیاده‌سازی تکمیل می‌شود)

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/synthetic_gen.py` | ایجاد | تسک ۲.۲ | — |

  | `tests/test_synthetic_gen.py` | ایجاد | بند ۷: V&V | — |

- **Result / Validation:** (پس از اجرا ثبت می‌شود)
