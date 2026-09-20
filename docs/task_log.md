# RideSafe-Bio — لاگ روزانه پیشرفت تسک‌ها

> هر تسک با چک‌لیست پلن تعریف و پس از پیاده‌سازی گام‌به‌گام تیک می‌خورد (بند ۱–۲ `rules.md`).
> قالب هر تسک: Goal / Checkpoints / Changes / Result-Validation.
> نشانگرها: ✅ اعتبارسنجی‌شده · ⏳ معلق (تأیید استاد / نسخه استاندارد / سورس قبلی).

**آخرین بازنگری:** 2026-09-14

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


### UX Fix — تب Signal (بازخورد کارفرما) ✅



- **Goal:** رفع سردرگمی نمایش ۵۰ سطر صفر اول (سیگنال‌های با سکون ابتدایی) و فراهم‌سازی دانلود کامل.

- **Checkpoints:**

  - [x] U1 — `st.dataframe` با کل دیتای فیلترشده (virtualization داخلی Streamlit).

  - [x] U2 — ۴ کارت خلاصه بالای تب Signal: Peak ax/ay/az + Total Duration.

  - [x] U3 — `st.download_button` برای CSV کامل فیلترشده.

- **Result / Validation:** بازخورد بصری کارفرما اعمال شد؛ دانلود دیگر محدود به ۵۰ سطر صفر نیست.



### Task 4.2 — نمودارهای تعاملی Plotly ✅



- **Goal:** سری زمانی تعاملی سه‌محوره با سایه‌زنی قرمز بازه‌های ناقض (B.5/B.6) + پراکندگی ۳بعدی بردار شتاب در برابر بیضی B.6 با تفکیک سبز/قرمز — رندر زیر ۱ ثانیه.

- **Checkpoints:**

  - [x] T1 — `plot_time_series`: ۳ trace (Scattergl برای پرف) + vrect قرمز نیمه‌شفاف به‌ازای هر بازه ناقض Jerk/3D + خاکستری برای transients مستثنی B.16.

  - [x] T2 — `plot_3d_ellipsoid`: Scatter3d دوگروهی سبز (داخل) / قرمز × (خارج) + Mesh3d سطح بیضی با adm per-sample (midpoint) + downsample هوشمند به 8000 نقطه.

  - [x] T3 — اتصال: Signal → سری زمانی؛ Evaluation → ۳بعدی.

  - [x] T4 — ۶ آزمون ساختار/پرف — همه پاس.

  - [x] T5 — Changes/Result + roadmap + commit `feat: ...` + پوش + smoke سرور.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `app.py` | +plot_time_series و plot_3d_ellipsoid و adm exposure در pipeline + UX fix تب Signal | تسک ۴.۲ + بازخورد UX | +۲۰۰ خط |

  | `tests/test_app.py` | +۶ آزمون نمودار (ساختار + پرف) | بند ۷ | ۱۵/۱۵ |

- **Result / Validation:** ۱۱۰/۱۱۰ کل پروژه (۱۵ تست UI). vrectها = بازه‌های ناقض واقعی (۲ jerk روی data_jerk_violation)؛ تفکیک ۳بعدی: safe dataset → صفر نقطه قرمز؛ پرف تولید هر دو figure < 1s (تست timeit). رفع باگ حین TDD: key ناهمسان `violation_intervals` (jerk) در برابر `triaxial_violations` (3D). Smoke سرور: HTTP 200 + health ok + صفر Traceback. plotly فقط در app.py — `src/` UI-free (بند ۴).


### Task 4.3 — پنل «شناسنامه ریسک و کارنامه ایمنی دستگاه» ✅



- **Goal:** تب Risk Passport رسمی: بنر انطباق کلی PASS/NON-COMPLIANT + Badge رنگی RB (پالت اختصاصی؛ قرمز فقط برای FAIL) + جدول per-axis + کارت الزامات مهار با متریک Active Requirements + جدول ردیابی نقض‌ها.

- **Checkpoints:**

  - [x] T1 — Badge: `build_risk_badge_html` (خالص، تست‌پذیر) با پالت `RB_BADGE_COLORS` (RB-1 بنفش #6a1b9a، RB-2 نارنجی #e65100، RB-3 فیروزه‌ای #0277bd، RB-4 زمردی #2e7d32).

  - [x] T2 — بنر انطباق: `build_compliance_banner_html` (سبز PASS / قرمز NON-COMPLIANT) — معیار: هر چهار معیار jerk/dose/recovery/3D.

  - [x] T3 — `build_per_axis_table`: DataFrame با رنگ شرطی + ردیف خاکستری «not evaluated» برای محورهای غایب (به‌جای st.json).

  - [x] T4 — کارت الزامات: متریک «Active Requirements: n of m» + آیتم‌های 🟠 فعال / ⚪ غیرفعال با شرط، بند و note مدت‌نامشخص.

  - [x] T5 — جدول ردیابی: ستون‌های Rule/Start Time/End Time/Peak Value/Clause از سه منبع نقض (Jerk/3D/dose-recovery).

  - [x] T6 — ۴ آزمون جدید (مجموع ۱۸ UI) + smoke سرور.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `src/config.py` | RB_BADGE_COLORS | پالت مصوب کارفرما | — |

  | `app.py` | ۳ تابع خالص HTML/table + بازطراحی tab_passport | تسک ۴.۳ | +۹۰ خط |

  | `tests/test_app.py` | +۴ آزمون پنل | بند ۷ | ۱۸/۱۸ |

- **Result / Validation:** ۱۱۴/۱۱۴ کل پروژه (۱۸ تست UI). تست‌ها: رنگ صحیح هر RB در HTML، عدم وجود قرمز FAIL در badge (تفکیک معنایی از classification) — پالت قرمز #b71c1c فقط در banner NON-COMPLIANT. متن PASS/NON-COMPLIANT و fallback خاکستری محورهای غایب آزمون شد. Smoke سرور: HTTP 200 + health ok + صفر Traceback. UI-free بودن src/ حفظ شد (بند ۴).


### Task 4.4 — ماژول صدور گزارش نهایی خودکار (Export Report) ✅



- **Goal:** خروجی دوگانه (تصمیم کارفرما): JSON ساخت‌یافته (منبع حقیقت Technical Passport) + متن خلاصه چاپی یک‌صفحه‌ای — با نام فایل زمان‌دار `ridesafe_report_YYYYMMDD_HHMM` و دکمه‌های دانلود در انتهای تب Risk Passport؛ بدون وابستگی جدید.

- **Checkpoints:**

  - [x] T1 — `build_report(results) -> dict`: report_type/generated_at/standard + signal (fs، n_samples، duration، inversions، mapping) + verdicts (jerk_b5/dose_b15/combined_b6 با بازه‌های ناقض) + risk (acceleration_rb/overall_rb/extremity/test_required) + restraints.

  - [x] T2 — `build_text_report(results, source_name) -> str`: سربرگ رسمی، Overall Verdict، RB + extremity، سه معیار PASS/FAIL، الزامات `[x]/[ ]`، جدول ردیابی.

  - [x] T3 — `report_file_stem()`: قالب زمانی مصوب + دو `st.download_button` با آیکون (📄 JSON / 📝 Text).

  - [x] T4 — ۷ آزمون جدید (مجموع ۲۵ UI): ساختار، serializability، قطعیت (حذف timestamp)، تطابق فیلدها با موتور، متن شامل حکم/RB، flag شدن NON-COMPLIANT روی data_jerk_violation، الگوی نام فایل.

  - [x] T5 — Changes/Result + roadmap (✅ ۴.۴، **بستن فاز ۴**) + commit + پوش.

- **Changes:**

  | فایل | تغییر | دلیل | نتیجه |

  |---|---|---|---|

  | `app.py` | +build_report و build_text_report و report_file_stem + دکمه‌های Export | تسک ۴.۴ + تصمیم‌های کارفرما | +۱۳۵ خط |

  | `tests/test_app.py` | +۷ آزمون گزارش | بند ۷ | ۲۵/۲۵ |

- **Result / Validation:** ۱۲۱/۱۲۱ کل پروژه (۲۵ تست UI). تست قطعیت: دو گزارش از یک دیتاست بجز generated_at برابرند. تست صحت: RB و impulse_count گزارش == خروجی موتور. NON-COMPLIANT + `FAIL] Jerk B.5` در گزارش متنی data_jerk_violation تأیید شد. Smoke سرور: HTTP 200 + health ok + صفر Traceback. UI-free بودن src/ (بند ۴). **فاز ۴ بسته شد.**

### Task 4.5 — Axis Convention guide figure ✅

- **Goal:** راهنمای تصویری دو پنل دوبعدی (Top X/Y + Side X/Z) بالای تب‌ها در `st.expander` با لیبل‌های انگلیسی و کپشن placement/invert؛ بدون تغییر `src/` و بدون وابستگی جدید.
- **Checkpoints:**
  - [x] T001 — branch `chatbox/axis-guide-4.5` + baseline ۱۲۱/۱۲۱
  - [x] T004 — `tests/test_axis_guide.py` (failing-first: ۵ fail / ۱ pass، فقط src UI-free سبز)
  - [x] T005/T006 — `assets/axis_guide.svg` (دو پنل X/Y + X/Z، لیبل‌های FR-004) + expander بالای تب‌ها با first-visit flag و fallback متنی
  - [x] T007 — ۶/۶ سبز؛ T008/T009 — caption سه‌اتمی (placement + Invert + sign-flips)؛ T010/T011 — رنگ‌های ColorContract
  - [x] T012 — suite کامل ۱۲۷/۱۲۷؛ T013 — smoke روی 8511 (HTTP 200، صفر Traceback)؛ T014 — viewport باریک 480px بدون clipping + sharpness زوم
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `assets/axis_guide.svg` | ایجاد (دو پنل تخت X/Y + X/Z، شش پیکان، لیبل‌های دقیق انگلیسی) | تسک ۴.۵ (US1/US3) | ۷۹۶۵ بایت، self-contained |
  | `app.py` | +ثابت‌ها و دو helper خالص (`load_axis_guide_svg`، `build_axis_guide_fallback_markdown`) + بلاک expander بین title و tabs | تسک ۴.۵ (US1/US2) | رندر inline SVG + fallback + caption |
  | `tests/test_axis_guide.py` | ایجاد (۶ آزمون: asset/XML، توکن‌ها، body-feel، wiring، رنگ‌های ممنوعه، UI-free بودن src) | بند ۷ + FR-009 | ۶/۶ سبز |
- **Result / Validation:** ۱۲۷/۱۲۷ کل پروژه (۱۲۱ baseline + ۶ جدید). رندر زنده تأیید شد: expander بازشونده بالای تب‌ها، SVG واقعی ۸۷۱×۵۶۹ در DOM، caption با هر سه اتم، viewport باریک ۴۱۴px بدون clipping. Smoke: HTTP 200 روی 8511 + صفر Traceback در لاگ. `src/` دست‌نخورده (بند ۴).

---

## فاز ۵ — یکپارچگی 17842 و مقایسه دونمایی

### Task 5.0 — ارزیابی تشخیصی داده لاگر مهندس حکمت (پیش‌فاز ۵) ⏳

- **Goal:** سنجش سازگاری لایه Ingestion و رفتار موتور 17929 روی داده‌های واقعی/سنتتیک حکمت (`Acceleration effects on passengers/`) قبل از هر تغییر کد. خط قرمز مأموریت: `src/` و `app.py` دست‌نخورده، هسته UI-free، بیس‌لاین ۱۲۷ سبز.
- **Checkpoints:**
  - [x] Data discovery — فرمت: `<HH:MM:SS.mmm> <counter>,ax,ay,az,<9 فیلد متادیتا>`؛ لاگر واقعی 100 Hz (کاونتر +10ms/خط، واحد ms)، سنتتیک 50 Hz؛ اعوجاج زمانی 0–30ms، ریزش خطوط (تا 1.2s)، گپ 5.7 دقیقه‌ای در sled_r1، dt منفی تا −8ms (coast_r2)
  - [x] Probe بند ۵ — `standardize_signal_frame` روی زمان متنی → `ValueError`؛ لودر `app.py` هم col0 ترکیبی زمان+کاونتر را نگاشت کامل نمی‌کند
  - [x] `scripts/evaluate_hekmat_samples.py` — پارس، جداسازی segment در گپ>1s، رسampling یکنواخت (الزام FR-2 هم‌فاصله‌سازی)، وارونگی az (سکون −1g → قرارداد +Z راهنمای محورها)، اجرای کامل موتور
  - [x] گزارش مقایسه‌ای ۷ دیتاست (2 سنتتیک + 3 سورتمه + 2 صاعقه) در ترمینال
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `scripts/evaluate_hekmat_samples.py` | ایجاد — اسکریپت تشخیصی موقت | گام ۳ مأموریت | ۸.۳KB، خارج از `src/`، بدون import UI |
  | `docs/task_log.md` | همین ورودی | بند ۲ قرارداد | — |
- **Result / Validation:** ۱۲۷/۱۲۷ پاس؛ `git diff` پاک. یافته‌های کلیدی: sim_unsafe → FAIL واقعی (B.5 + B.6 با ratio 6.0، RB-1) مطابق مقصود سازنده؛ سورتمه/صاعقه با موتور فعلی غالباً RB-1 (رانش: ay ≥ 1g)؛ دوز B.15 غیرتفکیکی روی راندهای تکی (≤490 از 11129 g·s)؛ ریکاوری بدون نتیجه (هیچ پالس ≥5g)؛ B.6 روی داده واقعی همگی با استثنای B.16 pass می‌شود. **ریسک موتور:** معیار لحظه‌ای jerk روی لرزش واقعی بیش‌فعال است (تا 49 g/s، 41 بازه در sled_r2) در حالی که تذکر کارفرما ارزیابی را «شیب پاکت/میانگین بازه» می‌داند؛ جهت x/y سنسور تأیید نشده و حکم RB به آن وابسته است. **گپ‌های فاز ۵:** پارس زمان متنی، حذف dt تکراری/منفی، جداسازی segment، رسampling یکنواخت، استخراج fs از کاونتر (نه میانه wall-clock)، تعیین جهت نصب x/y با کارفرما.

### Bugfix — کلیدهای قطبیت ±ax در پایپ‌لاین داشبورد ✅

- **Goal:** کشف نوبت ۵.۰: `run_evaluation_pipeline` کلیدهای `+ax/−ax` را در dict پیک‌ها نمی‌ساخت؛ در نتیجه قاعده مهار «−ax ≥ 2» (B.26 میله لگن) از داشبورد هرگز فعال نمی‌شد در حالی که موتور و تشخیصی هر دو سالم بودند.
- **Checkpoints:**
  - [x] تست failing-first در `tests/test_app.py` (`test_pipeline_surfaces_hard_braking_lap_bar`) — پیش از اصلاح با `KeyError: '-ax'` شکست خورد
  - [x] اصلاح `run_evaluation_pipeline`: ساخت کلیدهای قطبیت برای ax و az (+ نگه‌داشتن کلید بزرگی برای سطرهای متقارن Table B.1)
  - [x] suite کامل ۱۲۸/۱۲۸ پاس
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `app.py` | حلقه پیک‌ها: `peaks[axis]` بزرگی + کلیدهای `±ax` و `±az` | قاعده B.26 از داشبورد قابل‌فعال‌شدن شود | −ax=2.5g → lap bar met=True |
  | `tests/test_app.py` | +۱ آزمون ترمز شدید (−2.5g → −ax≥2 و lap bar) | بند ۷: رفتار قابل‌مشاهده مصرف‌کننده | failing-first → سبز |
- **Result / Validation:** ۱۲۸/۱۲۸ کل پروژه. ترمز شدید مصنوعی (−2.5g پلاتو، +ax=0) از مسیر کامل پایپ‌لاین داشبورد شناسایی و قاعده B.26 فعال شد. `src/` دست‌نخورده.

### Task 5.1 — تبدیل زمان لاگر حکمت به ثانیه (specs/002-add-timestamp-parser) ✅

- **Goal:** مرحله ingestion هسته یک ستون زمان از نوع ساعتِ دیواری (`HH:MM:SS(.mmm)?(\s+\d+)?` — شامل توکن چسبنده زمان+کاونتر طبق جلسه clarify) را به ثانیه نسبی float64 تبدیل کند؛ مرتب‌سازی پایدار با حفظ تعداد ردیف؛ رد صریح rollover/داده خراب؛ متادیتای ردیابی. خارج از دامنه: رسampling، جداسازی گپ، fs از کاونتر.
- **Checkpoints:**
  - [x] T001 ثبت پلن (این ورودی)
  - [x] T002 بیس‌لاین ۱۲۸/۱۲۸ پیش از تغییر
  - [x] T003–T004 فیکسچرهای مرجع + سنجاق passthrough عددی
  - [x] T005–T009 US1: تست failing-first تبدیل + `convert_clock_timestamps` + ادغام در `standardize_signal_frame` + متادیتا + تست انتگرال
  - [x] T010–T013 US2: sort پایدار/گره/اعوجاج + حفظ ردیف روی ۷ فایل مرجع
  - [x] T014–T016 US3: خطاهای شماره‌خط‌دار + رد rollover با آستانه
  - [x] T017–T021 اسموک کارایی، رگرسیون کامل، docs، بازنشستگی اسکریپت تشخیصی، commit
- **Changes:**
  | فایل | تغییر | دلیل | نتیجه |
  |---|---|---|---|
  | `src/preprocessing.py` | +`convert_clock_timestamps` (گرامر `^HH:MM:SS(.mmm)?(\s+\d+)?$`، تشخیص per-value، رد mixed/malformed/rollover) + پارامتر `rollover_threshold_s` در `standardize_signal_frame` + sort پایدار + متادیتای ۶ کلیدی | FR-001..FR-007 | مقادیر خروجی هم‌تراز ورودی، نسبی به زودترین نمونه |
  | `tests/test_preprocessing.py` | +۱۵ آزمون (فیکسچر ۷ فایل مرجع با skip دوستانه، passthrough، تبدیل، متادیتا، انتگرال، sort/گره/اعوجاج، خطاها، rollover، کارایی) | بند ۷ + contracts/test-contract | ۱۴۳/۱۴۳ |
  | `specs/002-add-timestamp-parser/*` | spec + plan + research + data-model + contracts + quickstart + tasks (۱۹/۲۱ تسک کد، T020 پاک‌سازی) | گردش‌کار speckit | ثبت‌شده |
  | `docs/roadmap.md` | سطر ۵.۰ ingestion در جدول فاز ۵ | بند ۲ | — |
- **Result / Validation:** ۱۴۳/۱۴۳ کل پروژه (۱۲۸ بیس‌لاین + ۱۵ جدید) — صفر رگرسیون. Failing-first واقعی در T005 مشاهده شد (ImportError → سپس ValueError مسیر numeric). دو اشکال حین TDD کشف و رفع شد: (۱) بررسی «ستون ترکیبی عدد+ساعت» در بازنویسی اولیه جامانده بود؛ (۲) تفریق اولین نمونه پیش از sort، جفت‌شدگی زمان/شتاب را در ورودی نامرتب به‌هم می‌ریخت — راه‌حل: هلپر مقادیر هم‌تراز با ورودی و نسبی به زودترین نمونه برمی‌گرداند و `standardize_signal_frame` با `sort_values(kind="stable")` تایم‌لاین نهایی غیرنزولی می‌سازد. کارایی: تبدیل 48k سطر < 2s (تست suite). US2/US3 چون هلپر طبق قرارداد کامل پیاده شده بود، به‌عنوان pin رگرسیون سبز شدند (انحراف مستند از failing-first). UI-free بند ۴ حفظ شد.
