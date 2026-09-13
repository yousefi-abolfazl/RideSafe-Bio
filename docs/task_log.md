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


### Task 2.2 — اسکریپت شبیه‌ساز داده شتاب `src/synthetic_gen.py` ✅



- **Goal:** ماژول تولید سیگنال شتاب سنتتیک با چهار شکل‌موج پایه (سینوسی، ذوزنقه‌ای، اسپایک گذرا، نویز گاوسی) — پارامترپذیر، قطعی (seed) و UI-free — به‌عنوان پیش‌نیاز تولید ۴ دیتاست مرزی تسک ۲.۳ و آزمون رگرسیون موتورهای فاز ۳/۵.

- **Checkpoints:**

  - [x] T1 — API پنج تابع خالص با قرارداد `(fs, duration, ..., seed) -> pd.DataFrame` (ستون‌های `time,ax,ay,az`).

  - [x] T2 — پالس ذوزنقه‌ای با `ramp_rate_g_per_s` پارامتر (بدون هاردکد 7/10/15).

  - [x] T3 — `tests/test_synthetic_gen.py`: ۲۲ آزمون قطعی — همه پاس.

  - [x] T4 — Changes/Result ثبت شد + commit `feat: ...` + پوش خودکار.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/synthetic_gen.py` | ایجاد — ۵ تابع: `generate_sine_wave`، `generate_trapezoid_pulse`، `generate_transient_spike`، `add_gaussian_noise`، `generate_composite_signal` | تسک ۲.۲ + سه تصمیم تأییدشده کارفرما | ۶.۴KB |

  | `tests/test_synthetic_gen.py` | ایجاد — ۲۲ آزمون واحد | بند ۷: V&V | همه پاس |

- **Result / Validation:** ۲۲/۲۲ آزمون پاس (۳۶/۳۶ کل پروژه): بازسازی دامنه/فرکانس/نرخ شیب، شکل خیز-پلاتو-افت، قطعیت seed، ابرپوشش خطی بدون clamp (دامنه ترکیبی > ۳g از اجزای ۳g اثبات شد)، آمار نویز (μ≈0، σ≈std)، محدوده‌های خطای پارامتر. بررسی خودکار: UI-free (بند ۴). Smoke دستورالعمل ۴ دیتاست ۲.۳ موفق.


### Task 2.3 — تولید و ذخیره ۴ دیتاست مرزی استاندارد ✅



- **Goal:** تولید چهار CSV قطعی در `data/` با `src/synthetic_gen.py` — هر دیتاست دقیقاً یک قاعده استاندارد را نقض کند و بقیه را پاس؛ مبنای آزمون رگرسیون دائمی موتورهای فاز ۳/۵ (بند ۷ قرارداد).

- **مشخصات (fs=500 Hz، واحد g، seed=42):**

  | دیتاست | ترکیب | قاعده نقض | قواعد پاس |

  |---|---|---|---|

  | `data_safe_family.csv` | ۲ پالس ذوزنقه‌ای az: 1.5g، 4 g/s، افت کامل + نویز σ=0.02 | هیچ (کنترل منفی) | B.5/B.7، B.15، B.6، 17842 |

  | `data_jerk_violation.csv` | ۱ پالس az: 1.5g با شیب 18 g/s | B.5 (سقف 15 g/s) | دامنه زیر پاکت؛ 17842 کور |

  | `data_3d_combined_violation.csv` | سینوس هم‌فاز 0.8Hz: ax=1.2g، ay=0.5g، az=1.7g | فقط B.6 (xyz=1.13>1) | تک‌محوره و هر سه جفتی ≤ 1 |

  | `data_cumulative_dose_violation.csv` | ۳ پالس 5g/7g·s⁻¹ زنجیره‌شده روی عبور 2g | B.15 (min بین پالس‌ها = 2.0g) | تک‌تکانه‌ای و نرخ مجاز |

- **Checkpoints:**

  - [x] T1 — `src/datasets.py`: ۴ سازنده + `build_all_datasets(output_dir, seed)`.

  - [x] T2 — شناسنامه: هر سازنده dict (دامنه‌ها، نرخ، فواصل) برمی‌گرداند.

  - [x] T3 — `tests/test_datasets.py`: ۱۸ آزمون اعتبارسنجی ریاضی روی CSV.

  - [x] T4 — ۴ فایل CSV تولید و commit شدند.

  - [x] T5 — roadmap آپدیت + commit + پوش خودکار.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/datasets.py` | ایجاد | تسک ۲.۳ | ۴.۹KB |

  | `tests/test_datasets.py` | ایجاد | بند ۷ | ۱۸ پاس |

  | `data/*.csv` ×۴ | ایجاد | خروجی رسمی فاز ۲ | ۵۳۶KB مجموع |

- **Result / Validation:** ۱۸/۱۸ آزمون پاس (۵۴/۵۴ کل پروژه). ادعاها مستقیماً از CSV بازمحاسبه شدند: شیب برازش‌شده 3.97/17.99/7.0 g/s؛ نسبت بیضوی سه‌محوره 1.13>1 با هر سه جفتی ≤1؛ کمینه بین‌پالسی دقیقاً 2.0g (بدون ریکاوری)؛ قطعیت sha256 دو اجرا. اصلاح طراحی مهم: نسخه اولیه dose شکاف صفر بین پالس‌ها داشت (ریکاوری کامل = پاس اشتباهی!)؛ زنجیره‌کردن شروع پالس بعدی به لحظه عبور 2g نقض واقعی B.15 را تضمین کرد. UI-free (بند ۴). **فاز ۲ بسته شد.**


---



## فاز ۳ — هسته نوآورانه ISO 17929



### Task 3.1 — ماژول Jerk (نرخ خیز/افت شتاب) ✅



- **Goal:** پیاده‌سازی `calculate_jerk_rate()` و `evaluate_jerk_compliance()` در `src/iso17929_engine.py` — مشتق زمانی da/dt پس از فیلتر 5 Hz و ارزیابی در برابر نرخ‌های 7/10/15 g/s پیکربندی‌پذیر (B.5).

- **Checkpoints:**

  - [x] T1 — `src/config.py`: `JERK_LIMITS` (family=7، general=10، extreme=15) + `JERK_MIN_RATE=1.0` + `JERK_CLAUSE`.

  - [x] T2 — `src/iso17929_engine.py`: `calculate_jerk_rate` (np.gradient مرکزی، صفر-فاز) + `evaluate_jerk_compliance` (فقط `|jerk| > limit` طبق تذکر کارفرما؛ `JERK_MIN_RATE` صرفاً هندسی، نقض نیست).

  - [x] T3 — `tests/test_iso17929_engine.py`: ۱۱ آزمون — همه پاس.

  - [x] T4 — Changes/Result + roadmap + commit `feat: ...` + پوش خودکار.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/config.py` | افزودن JERK_LIMITS / JERK_MIN_RATE / JERK_CLAUSE | بند ۶ | — |

  | `src/iso17929_engine.py` | ایجاد — ۲ تابع + `_contiguous_intervals` | تسک ۳.۱ | ۳.۶KB |

  | `tests/test_iso17929_engine.py` | ایجاد — ۱۱ آزمون | بند ۷ | همه پاس |

- **Result / Validation:** ۱۱/۱۱ پاس (۶۵/۶۵ کل پروژه): مشتق سینوس با خطای نسبی < 1% در برابر جواب تحلیلی A·ω·cos؛ پلاتو ذوزنقه jerk≈0؛ دیتاست `data_jerk_violation` (18 g/s) با هر سه کلاس FAIL و ≥2 بازه ناقض با `clause="ISO 17929 §B.5"`؛ `data_safe_family` با کلاس خانوادگی PASS؛ شروع ملایم 0.3 g/s (زیر JERK_MIN_RATE) ناقض ثبت نشد — تذکر کارفرما اعمال شد. کشف مهم: فیلتر تک‌گذره کازوال rampe خطی را به S-منحنی تبدیل می‌کند و پیک لحظه‌ای jerk تا ~1.1× نرخ اسمی می‌رسد — در تست با باند S-curve پوشش داده شد؛ ارزیابی B.5 بر مبنای شیب پاکت/میانگین بازه است نه پیک لحظه‌ای. UI-free (بند ۴).




### Task 3.2 — ماژول پالس و دوز شتاب (B.15) ✅



- **Goal:** آشکارساز تکانه با تفکیک خیز/پلاتو/افت (`detect_impulses` + dataclass `Impulse`) و ارزیابی دوز تجمعی (`compute_cumulative_dose`) طبق B.15 با ردیابی‌پذیری.

- **Checkpoints:**

  - [x] T1 — `src/config.py`: `IMPULSE_MIN_AMPLITUDE_G=0.2`، `RECOVERY_THRESHOLD_G=2.0`، `DOSE_TOLERANCE_GS=11129.0` (بازساخت‌شده A7)، `DOSE_CLAUSE`.

  - [x] T2 — `src/iso17929_engine.py`: dataclass `Impulse` + `detect_impulses` (گیت 0.2g + حداقل مدت 20ms + شکافتن پالس‌های زنجیره‌ای در دره‌های |a|) + `compute_cumulative_dose` (مساحت در برابر ظرفیت قابل override + قاعده ریکاوری تکانه‌های ≥5g).

  - [x] T3 — ۱۱ آزمون جدید — همه پاس.

  - [x] T4 — Changes/Result + roadmap + commit `feat: ...` + پوش خودکار.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/config.py` | افزودن IMPULSE/RECOVERY/DOSE + REPEATABLE floor | بند ۶ | — |

  | `src/iso17929_engine.py` | افزودن ماژول تکانه و دوز | تسک ۳.۲ | +~۱۹۰ خط |

  | `tests/test_iso17929_engine.py` | گسترش به ۲۲ آزمون | بند ۷ | همه پاس |

  | `data/data_cumulative_dose_violation.csv` | بازتولید — زنجیره 0.05s قبل از عبور 2g | نقض واقعی B.15 (min=2.35g) | آزمون‌های datasets همچنان پاس |

- **Result / Validation:** ۲۲/۲۲ پاس موتور (۷۶/۷۶ کل پروژه): مساحت ذوزنقه با جواب تحلیلی خطای <0.02 g·s؛ شمارش تکانه: safe=2، jerk=1، dose=3؛ نقض ریکاوری روی dose: ۲ بازه با min=2.35g>2.0 و `clause="ISO 17929 §B.15"`؛ safe_family: dose و ریکاوری کامل؛ override ظرفیت (0.01) → dose_compliant=False؛ قطعیت و impulse_id ترتیبی با `clause="ISO 17929 §B.4"`. اصلاحات طراحی: (۱) گیت نویز 20ms — نوسان 4ms حذف شد؛ (۲) پالس‌های زنجیره‌ای B.15 هرگز زیر آستانه نمی‌روند و در یک گیت ادغام می‌شدند — با شکافتن در دره‌های |a| (find_peaks) سه تکانه مجزا شناسایی شد. UI-free (بند ۴).


### Task 3.3 — ماژول نامساوی سه‌بعدی (بیضوی B.6) ✅



- **Goal:** پایش ترکیب همزمان سه محور: (ax/ax,adm)² + (ay/ay,adm)² + (az/az,adm)² ≤ 1.0 با adm وابسته به مدت از پاکت‌های گسسته B.11–B.14، استثنای < 0.2 s (B.16)، تفکیک نقض جفتی/سه‌بعدی.

- **Checkpoints:**

  - [x] T1 — `src/config.py`: `AXIS_PACKETS` (فرمت (duration_s, limit_g) صعودی — B.11–B.14، بازساخت‌شده) + `COMBINED_EXCLUSION_S=0.2` + `COMBINED_CLAUSE`.

  - [x] T2 — `lookup_adm(axis, polarity, duration_s)` (درون‌یابی np.interp؛ زیر اولین رأس → ماکزیمم، فراتر از آخرین → پایدا) + `evaluate_3d_combined_inequality(df, duration_s=None, exclusion_s)` (adm per-sample با قطبیت لحظه‌ای ax/az، مدت تعرض = override یا span بالای 0.2g همان محور؛ خروجی شامل sample_ratios برای داشبورد فاز ۴).

  - [x] T3 — ۸ آزمون جدید (مجموع ۳۰ در فایل) — همه پاس.

  - [x] T4 — Changes/Result + roadmap + commit + پوش.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/config.py` | AXIS_PACKETS + COMBINED_* | بند ۶ / V6 | — |

  | `src/iso17929_engine.py` | lookup_adm + evaluate_3d_combined_inequality + _exposure + _ratio_intervals | تسک ۳.۳ | +۱۳۵ خط |

  | `src/synthetic_gen.py` | پارامتر offset برای generate_sine_wave | ساخت دیتاست با بایاس +z | سازگار با تست‌های قبلی |

  | `src/datasets.py` + `data/data_3d_combined_violation.csv` | بازطراحی: ax=1.73+1.73sin، ay=1.1sin، az=1.9+1.9sin (بایاس مثبت +z) | نقض انحصاری B.6 | تکانه‌ها: jفت‌ها ≤1، سه‌بعدی >1 پایدار |

  | `tests/test_datasets.py` | به‌روزرسانی ادعاهای ۳بعدی | همگام با داده جدید | پاس |

- **Result / Validation:** ۸۴/۸۴ کل پروژه (۳۰ تست موتور). دیتاست جدید: سه بازه ناقض sustained (≥0.2s) با peak_ratio≈1.19، هر سه جفت XY/XZ/YZ ≤1 (0.78/0.88/0.71) — نقض انحصاری سه‌بعدی تأیید شد. safe_family کاملاً پاس. استثنای B.16: اسپایک 6g/0.1s با r3=1.078 → صرفاً excluded_transients، compliant=True. اصلاحات حین TDD: (۱) lookup_adm محور نامعتبر را بی‌سروصدا به y نگاشت می‌کرد → اعتبارسنجی صریح؛ (۲) داده قدیمی با adm per-sample اصلاً نقض نمی‌شد (z-term=0.1) → هندسه دیتاست با جست‌وجوی پارامتری بازطراحی شد؛ (۳) قطبیت منفی az پاکت -z (سقف 2g) را فعال می‌کرد → بایاس مثبت +z الزامی شد. UI-free (بند ۴).


### Task 3.4 — موتور رده‌بندی ریسک بیومکانیکی RB-1..RB-4 (Table B.1) ✅



- **Goal:** دسته‌بندی خودکار دستگاه در RB-1..RB-4 از Table B.1 بر پایه حداکثر دامنه‌های شتاب (خروجی detect_impulses) + متادیتای اختیاری سرعت — با استخراج الزامات مهاربند (V11) و نماد extremity؛ تفکیک acceleration_rb از overall_rb (تصمیم کارفرما).

- **Checkpoints:**

  - [x] T1 — `src/config.py`: `RB_ACCELERATION_TABLE` (بازه‌های [min,max) با مرز متعلق به رده بالاتر — تصمیم محافظه‌کارانه کارفرما؛ -az بدون باند عددی RB-4) + `RB_SPEED_TABLE` + `RB_EXTREMITY_MAP` + `RESTRAINT_REQUIREMENTS` (۶ قاعده V11) + `RB_CLAUSE`.

  - [x] T2 — `src/iso17929_engine.py`: dataclass `RiskAssessment` (acceleration_rb / overall_rb / extremity / per_axis_levels / metadata_status / test_required) + `classify_risk_level` (بدترین-حالت؛ متادیتا اختیاری) + `extract_restraint_requirements` (قواعد دامنه‌ای و دامنه×مدت با note برای مدت نامشخص).

  - [x] T3 — ۱۲ آزمون جدید (مجموع ۴۲ در فایل) — همه پاس.

  - [x] T4 — Changes/Result + roadmap + commit `feat: ...` + پوش.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/config.py` | RB_ACCELERATION_TABLE / RB_SPEED_TABLE / RB_EXTREMITY_MAP / RESTRAINT_REQUIREMENTS | بند ۶ / Table B.1 | — |

  | `src/iso17929_engine.py` | RiskAssessment + classify_risk_level + extract_restraint_requirements | تسک ۳.۴ | +۱۳۵ خط |

  | `tests/test_iso17929_engine.py` | گسترش به ۴۲ آزمون | بند ۷ | همه پاس |

- **Result / Validation:** ۴۲/۴۲ پاس موتور (۹۶/۹۶ کل پروژه). مرزها: ax=3.0→RB-1 و 2.9→RB-2 (قرارداد محافظه‌کارانه تاییدشده)؛ +az=1.9→RB-4 (اصلاح انتظار تست — <2g واقعاً RB-4 است)؛ -az: RB-4 فقط برای فقدان انحراف منفی (peak=0) — باند عددی catch-all حذف شد چون همه‌چیز را RB-4 می‌کرد. بدترین-حالت: +az=3.2 (RB-2) + سرعت 25m/s (RB-1) → overall=RB-1 با acceleration_rb=RB-2 و metadata_status متمایز. دیتاست‌ها: dose (5g)→RB-1، safe (1.57g)→RB-2/RB-3. مهاربند: +az=4.0→تکیه‌گاه سر+میله کمر met=True؛ 3.9→False؛ ay=1.2 بدون مدت → note «duration unknown». UI-free (بند ۴). **فاز ۳ بسته شد.**


---



## فاز ۴ — داشبورد تعاملی و گزارش‌گیری



### Task 4.1 — واسط کاربری Streamlit (بارگذاری + تنظیمات) ✅



- **Goal:** بازطراحی `app.py` به داشبورد کامل: بارگذاری CSV/TXT یا انتخاب دیتاست سنتتیک با یک کلیک (FR-1) + پنل تنظیمات نگاشت/وارونگی/واحد محورها (FR-2) — مصرف صرفاً از موتورهای `src/`؛ رابط انگلیسی فنی (تصمیم کارفرما).

- **Checkpoints:**

  - [x] T1 — معماری: sidebar تنظیمات + ۳ تب (Signal/Evaluation/Risk Passport)؛ بدنه اسکریپت در `render_dashboard()` (import-safe برای تست).

  - [x] T2 — منبع داده: file_uploader CSV/TXT با تشخیص جداکننده (`,`/`;`/tab/`\s+` رجکس) یا انتخاب سنتتیک + دکمه Generate & Load؛ نگاشت پویا از ستون‌های واقعی فایل.

  - [x] T3 — کنترل‌ها: وارونگی سه محور، واحد g/m/s² (تبدیل خودکار)، fs خودکار/دستی، کلاس دستگاه → JERK_LIMITS.

  - [x] T4 — پایپ‌لاین کامل `run_evaluation_pipeline()`: standardize → filter → jerk → impulses → dose → 3D → RB؛ نمایش metricهای PASS/FAIL + هشدار بازه‌های ناقض + transients مستثنی.

  - [x] T5 — `tests/test_app.py`: ۹ آزمون توابع خالص (delimiter، mapping، inversion، بارگذاری) — همه پاس.

  - [x] T6 — Changes/Result + roadmap + commit `feat: ...` + پوش + smoke.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `app.py` | بازطراحی کامل (۱۲KB) | تسک ۴.۱ + تصمیمات کارفرما | UI انگلیسی، import-safe |

  | `tests/test_app.py` | ایجاد — ۹ آزمون | بند ۷ | همه پاس |

- **Result / Validation:** ۱۰۵/۱۰۵ کل پروژه (۹ تست UI). Smoke سرور: `streamlit run app.py` پورت 8601 → HTTP 200 + health `ok` + صفر Traceback در لاگ. رفع باگ حین TDD: `str.split(r"\s+")` در پایتون لایترال است نه رجکس — تشخیص whitespace با `re.split` اصلاح شد (تست مرزی بود و شکست خورد/رفع شد). ساختار import-safe: `render_dashboard()` فقط در اجرای Streamlit صدا زده می‌شود؛ توابع خالص بدون runtime قابل تست‌اند. `src/` همچنان UI-free (بند ۴).
