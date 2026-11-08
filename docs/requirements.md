# Anonymous Confession Bot
## Software Requirements & Implementation Specification

**Document Version:** 1.0  
**Status:** Proposed / Ready for Technical Review  
**Project Type:** Telegram Bot  
**Architecture:** Modular Monolith  
**Primary Language:** Python  
**Target Deployment:** Linux VPS

---

# 1. Project Overview

## 1.1. معرفی پروژه

این پروژه یک ربات تلگرام برای دریافت، مدیریت، بررسی و انتشار پیام‌های ناشناس در یک کانال آنتی‌کراش است.

کاربران از طریق گفت‌وگوی خصوصی با ربات، پیام‌های متنی خود را ارسال می‌کنند. سیستم محتوای پیام‌ها را از نظر توهین، فحاشی، تهدید، آزار، محتوای نامناسب و افشای اطلاعات خصوصی بررسی می‌کند.

پس از انجام بررسی، پیام در صف مدیریت قرار می‌گیرد و ادمین‌های مجاز می‌توانند آن را تأیید، رد یا برای بررسی بیشتر علامت‌گذاری کنند.

پیام تأییدشده توسط ربات، بدون نمایش هویت فرستنده در کانال منتشر می‌شود.

سیستم شناسه عددی تلگرام فرستنده و ارتباط آن با پیام را به‌صورت امن و کنترل‌شده نگهداری می‌کند.

## 1.2. اهداف پروژه

اهداف اصلی:

1. فراهم‌کردن یک روش ساده برای ارسال پیام ناشناس.
2. جلوگیری از انتشار محتوای توهین‌آمیز یا آسیب‌زا.
3. ایجاد سیستم مدیریت پیام‌ها برای ادمین‌ها.
4. قابلیت شناسایی فرستنده توسط مسئولان مجاز در موارد ضروری.
5. ذخیره تاریخچه پیام‌ها و تصمیم‌های مدیریتی.
6. جلوگیری از اسپم و سوءاستفاده.
7. امکان توسعه قابلیت‌های آینده بدون تغییر اساسی معماری.

## 1.3. اصول طراحی

- **Privacy by Design:** حداقل‌سازی داده‌های هویتی و محدودیت دسترسی.
- **Security by Default:** بررسی مجوزها برای تمام عملیات حساس.
- **Separation of Concerns:** جداسازی منطق کسب‌وکار از رابط تلگرام و دیتابیس.
- **Maintainability:** ساختار ماژولار و قابل تست.
- **Observability:** ثبت رویدادها و خطاهای مهم بدون افشای محتوای خصوصی.
- **Reliability:** جلوگیری از پردازش تکراری و مدیریت خطاهای انتشار.
- **Simplicity:** اجتناب از پیچیدگی‌های غیرضروری در MVP.

---

# 2. Scope Definition

## 2.1. In-Scope — MVP

قابلیت‌های ضروری نسخه اولیه:

### User Features

- شروع ارتباط با ربات با `/start`
- نمایش قوانین و سیاست حریم خصوصی
- ثبت پذیرش قوانین
- دریافت پیام متنی از کاربر
- اعتبارسنجی اولیه پیام
- ثبت پیام در دیتابیس
- تولید شناسه عمومی و غیرقابل حدس برای پیگیری
- نمایش نتیجه ثبت پیام
- مشاهده وضعیت پیام‌های ارسال‌شده
- درخواست حذف پیام منتشرنشده
- نمایش راهنما و قوانین

### Moderation Features

- نرمال‌سازی متن فارسی
- تشخیص الگوهای ممنوعه
- تشخیص شماره تلفن، لینک و اطلاعات حساس
- بررسی محتوا با مدل هوش مصنوعی در صورت فعال‌بودن قابلیت
- دسته‌بندی پیام بر اساس نوع تخلف و سطح ریسک
- ثبت نتیجه بررسی خودکار
- ارسال پیام برای بررسی انسانی
- جلوگیری از انتشار خودکار محتوای پرریسک

### Admin Features

- احراز هویت ادمین بر اساس Telegram User ID
- بررسی پیام‌های در انتظار
- تأیید پیام
- رد پیام با دلیل
- ارجاع برای بررسی ویژه
- مشاهده اطلاعات فرستنده بر اساس مجوز
- مسدودسازی موقت یا دائم کاربر
- مشاهده سوابق یک پیام
- ثبت فعالیت‌های مدیریتی

### Publishing Features

- انتشار پیام تأییدشده در کانال
- عدم انتشار نام یا شناسه فرستنده
- ثبت شناسه پیام منتشرشده
- اطلاع‌رسانی نتیجه انتشار به کاربر
- مدیریت خطا و تلاش مجدد کنترل‌شده

### Infrastructure Features

- دیتابیس PostgreSQL
- ساختار مهاجرت دیتابیس
- تنظیمات مبتنی بر Environment Variables
- اجرای Docker
- سیستم Logging
- Health Check
- تست خودکار
- Backup و Recovery

## 2.2. Out-of-Scope — MVP

ویژگی‌های زیر در نسخه اولیه پیاده‌سازی نمی‌شوند:

- پنل مدیریت تحت وب
- پشتیبانی از تصویر و ویدئو
- پشتیبانی از پیام صوتی
- پیام‌های خصوصی ناشناس بین کاربران
- سیستم کامنت اختصاصی
- انتشار خودکار بدون تأیید ادمین
- سیستم امتیازدهی کاربران
- مدیریت چندین کانال
- سیستم پیشنهاد محتوای هوشمند
- اپلیکیشن موبایل مجزا
- معماری Microservices

---

# 3. Technology Stack

## 3.1. فناوری‌های پیشنهادی

| Component | Technology | Purpose |
|---|---|---|
| Programming Language | Python 3.12+ | زبان اصلی پروژه |
| Telegram Framework | aiogram 3.x | مدیریت ارتباط با Telegram API |
| Database | PostgreSQL | ذخیره داده‌ها |
| ORM | SQLAlchemy 2.x | دسترسی به دیتابیس |
| Migrations | Alembic | مدیریت تغییرات Schema |
| Validation | Pydantic 2.x | اعتبارسنجی داده‌ها |
| Configuration | pydantic-settings | مدیریت تنظیمات |
| Testing | pytest + pytest-asyncio | تست‌های خودکار |
| Code Quality | Ruff | Lint و Format |
| Containerization | Docker Compose | اجرای سرویس‌ها |
| Dependency Manager | uv | مدیریت وابستگی‌ها |
| Logging | Python logging / structlog | ثبت رویدادها |
| AI Provider | Configurable Adapter | پردازش محتوای متنی |

نسخه‌های دقیق وابستگی‌ها باید هنگام ایجاد پروژه انتخاب و در Lockfile ثبت شوند.

## 3.2. دلیل انتخاب معماری

معماری اصلی پروژه Modular Monolith خواهد بود.

در این معماری:

- کل سیستم در یک مخزن اصلی توسعه داده می‌شود.
- بخش‌های مختلف منطق مستقل و ماژولار هستند.
- تمام بخش‌ها می‌توانند در یک فرآیند اصلی اجرا شوند.
- ارتباط داخلی ماژول‌ها از طریق Interface و Service انجام می‌شود.
- وابستگی مستقیم منطق دامنه به Telegram API ممنوع است.
- اضافه‌کردن Worker جداگانه در آینده امکان‌پذیر خواهد بود.

استفاده از Microservices در MVP توصیه نمی‌شود؛ زیرا هزینه توسعه، نگهداری و دیباگ را بدون مزیت متناسب افزایش می‌دهد.

---

# 4. High-Level Architecture

## 4.1. Components

سیستم از اجزای اصلی زیر تشکیل می‌شود:

### Telegram Interface Layer

مسئول دریافت Updateها، مدیریت دستورات، ارسال پاسخ و پردازش دکمه‌های Inline.

این لایه نباید مستقیماً SQL اجرا کند یا تصمیم‌های کسب‌وکار را پیاده‌سازی کند.

### Application Layer

مسئول اجرای Use Caseها:

- SubmitMessage
- ModerateMessage
- ApproveMessage
- RejectMessage
- PublishMessage
- RestrictUser
- WithdrawMessage
- RequestIdentityAccess

### Domain Layer

شامل:

- مدل‌های دامنه
- وضعیت‌های پیام
- قوانین کسب‌وکار
- سیاست‌های انتشار
- سیاست‌های دسترسی
- تعریف خطاهای دامنه

### Infrastructure Layer

شامل:

- Repository Implementation
- PostgreSQL Session
- Telegram Gateway
- AI Provider Adapter
- Rate Limiter
- Configuration
- Logging

## 4.2. Dependency Rules

قوانین وابستگی:

1. Domain نباید به Telegram یا SQLAlchemy وابسته باشد.
2. Application می‌تواند از Interfaceهای Domain استفاده کند.
3. Infrastructure رابط‌های تعریف‌شده را پیاده‌سازی می‌کند.
4. Telegram Handler فقط Application Service را فراخوانی می‌کند.
5. تصمیم‌های دسترسی باید در لایه Application نیز اعتبارسنجی شوند.
6. تمام تغییرات حساس باید در Audit Log ثبت شوند.

---

# 5. Functional Modules

## 5.1. User Management

### Responsibilities

- شناسایی کاربر با شناسه عددی تلگرام
- ایجاد پروفایل داخلی در اولین تعامل
- مدیریت پذیرش قوانین
- بررسی وضعیت محدودیت‌ها
- مدیریت درخواست حذف داده
- ثبت حداقلی وضعیت فعالیت

### Business Rules

**USR-001:** هر Telegram User ID تنها یک رکورد فعال در جدول کاربران داشته باشد.

**USR-002:** تغییر Username نباید باعث ایجاد کاربر جدید شود.

**USR-003:** کاربر مسدودشده نباید پیام جدید ثبت کند.

**USR-004:** ارسال پیام بدون پذیرش قوانین مجاز نیست.

**USR-005:** Username، شماره تلفن و نام نمایشی برای عملکرد اصلی الزامی نیستند و نباید بدون ضرورت نگهداری شوند.

**USR-006:** سیستم باید قابلیت غیرفعال‌سازی یا حذف داده‌های غیرضروری کاربر را بر اساس سیاست نگهداری داشته باشد.

## 5.2. Message Submission

### Input

- Telegram User ID
- Message Text
- Telegram Message ID
- Telegram Update ID
- Timestamp

### Validation

قوانین پیشنهادی:

- پیام باید از چت خصوصی دریافت شده باشد.
- محتوای پیام فقط متن باشد.
- پیام خالی یا فقط شامل فاصله پذیرفته نشود.
- حداقل طول متن: ۵ کاراکتر.
- حداکثر طول متن: ۲۰۰۰ کاراکتر.
- پیام نباید از سقف Rate Limit عبور کند.
- کاربر نباید دارای محدودیت فعال باشد.

حداقل و حداکثر طول و محدودیت‌های ارسال باید Configurable باشند.

### Output

در صورت موفقیت:

- ثبت پیام
- تولید Submission ID
- قرارگیری در وضعیت `RECEIVED`
- ارسال رسید ثبت پیام برای کاربر

### Error Cases

- MessageTooShort
- MessageTooLong
- UserRestricted
- RateLimitExceeded
- UnsupportedMessageType
- DuplicateSubmission
- DatabaseUnavailable

پیام‌های خطا باید برای کاربر فارسی، واضح و بدون افشای جزئیات داخلی باشند.

## 5.3. Content Moderation

### Processing Pipeline

1. دریافت Submission.
2. بررسی اعتبار و طول متن.
3. نرمال‌سازی متن.
4. اجرای قوانین قطعی.
5. استخراج نشانه‌های محتوای حساس.
6. اجرای AI Moderation در صورت فعال‌بودن.
7. ادغام نتایج بررسی.
8. تعیین سطح ریسک.
9. ثبت نتیجه در دیتابیس.
10. انتقال به صف بررسی ادمین.

### Persian Text Normalization

سیستم باید موارد زیر را پشتیبانی کند:

- تبدیل حروف عربی معادل به فارسی
- یکسان‌سازی فاصله‌ها
- مدیریت نیم‌فاصله
- حذف یا مدیریت نویسه‌های کنترلی نامرئی
- شناسایی شکل‌های متفاوت ارقام
- تشخیص کشیدگی غیرعادی حروف
- مدیریت علائم نگارشی تکراری
- پشتیبانی پایه از Finglish

نسخه اصلی پیام نباید با متن نرمال‌شده جایگزین شود.

### Moderation Categories

- `PROFANITY`
- `HARASSMENT`
- `THREAT`
- `HATE`
- `SEXUAL_CONTENT`
- `PERSONAL_INFORMATION`
- `SPAM`
- `SCAM`
- `IMPERSONATION`
- `SENSITIVE_CONTENT`
- `OFF_TOPIC`
- `UNKNOWN`

### Moderation Decision

خروجی استاندارد:

- فهرست دسته‌های شناسایی‌شده
- شدت هر دسته
- سطح کلی ریسک
- توضیح کوتاه
- منبع تشخیص
- نسخه قوانین یا مدل
- وضعیت موفقیت یا خطای پردازش

سطوح ریسک:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

### Moderation Rules

**MOD-001:** تمام پیام‌های MVP قبل از انتشار نیازمند تأیید انسانی هستند.

**MOD-002:** نتیجه مدل AI نباید مستقیماً وضعیت انتشار را تغییر دهد.

**MOD-003:** خطای سرویس AI نباید باعث انتشار بدون بررسی شود.

**MOD-004:** خطای AI باید به‌صورت مستقل ثبت شود.

**MOD-005:** وجود نشانه اطلاعات خصوصی شخص ثالث باید پیام را برای بررسی ویژه علامت‌گذاری کند.

**MOD-006:** نتیجه AI صرفاً پیشنهاد است و تصمیم نهایی ادمین باید ثبت شود.

**MOD-007:** پیام‌های دارای تهدید جدی نباید با یک تأیید معمولی منتشر شوند.

**MOD-008:** متن اصلی و نتیجه پالایش باید از یکدیگر مستقل ذخیره شوند.

## 5.4. Admin Management

### Roles

#### OWNER

- مدیریت تمام تنظیمات
- ایجاد و حذف ادمین
- تعیین مجوزها
- مشاهده هویت فرستنده در چارچوب سیاست ثبت‌شده
- مشاهده Audit Log
- اعمال محدودیت
- مدیریت سیاست‌های نگهداری

#### SENIOR_ADMIN

- مدیریت تخلفات
- مشاهده سوابق کاربران در چارچوب مجوز
- اعمال محدودیت
- بررسی پیام‌های حساس
- مشاهده گزارش‌های مدیریتی

#### MODERATOR

- مشاهده پیام‌های در انتظار
- تأیید یا رد پیام
- ثبت دلیل تصمیم
- ارجاع پیام مشکوک
- بدون دسترسی به شناسه واقعی فرستنده

#### PUBLISHER

- مشاهده پیام‌های تأییدشده
- انتشار پیام‌ها
- مشاهده وضعیت انتشار
- بدون دسترسی به شناسه واقعی فرستنده

### Permission Requirements

- تمام عملیات باید در زمان اجرا مجوزسنجی شوند.
- شناسه Telegram ادمین معیار شناسایی باشد.
- نقش نباید صرفاً از طریق Callback Data تعیین شود.
- تغییر نقش‌ها باید در Audit Log ثبت شود.
- مجوز مشاهده هویت از مجوز مشاهده متن مستقل باشد.

## 5.5. Publishing

### Responsibilities

- دریافت پیام تأییدشده
- آماده‌سازی قالب انتشار
- بررسی وضعیت و مجوز انتشار
- ارسال پیام جدید به کانال
- ثبت نتیجه
- اطلاع‌رسانی به فرستنده

### Publishing Format

نمونه:

**💌 پیام ناشناس #A1042**

متن پیام...

`#ناشناس #آنتی_کراش`

در نسخه اولیه:

- نام فرستنده نمایش داده نشود.
- Username فرستنده منتشر نشود.
- شناسه عددی او در متن یا Metadata برنامه قرار نگیرد.
- پیام جدید با هویت ربات در کانال ایجاد شود.
- متن پیام قبل از انتشار از نظر قالب‌بندی و نشانه‌های افشای اطلاعات بررسی شود.

### Reliability Rules

**PUB-001:** فقط پیام‌های تأییدشده قابل انتشار باشند.

**PUB-002:** انتشار باید دارای شناسه عملیات مستقل باشد.

**PUB-003:** عملیات انتشار هم‌زمان یک پیام باید کنترل شود.

**PUB-004:** پس از انتشار موفق، Telegram Channel Message ID ذخیره شود.

**PUB-005:** در صورت Timeout نامشخص، ارسال مجدد نباید بدون بررسی احتمال انتشار قبلی انجام شود.

**PUB-006:** در صورت خطای قطعی، عملیات با سیاست Retry محدود انجام شود.

**PUB-007:** حذف یا ویرایش پیام منتشرشده باید عملیات مستقل و قابل Audit باشد.

---

# 6. Message State Machine

## 6.1. Review Status

- `RECEIVED`
- `SCREENING`
- `PENDING_REVIEW`
- `ESCALATED`
- `NEEDS_EDIT`
- `APPROVED`
- `REJECTED`
- `WITHDRAWN`

## 6.2. Publication Status

- `NOT_QUEUED`
- `QUEUED`
- `PUBLISHING`
- `PUBLISHED`
- `FAILED`
- `UNCERTAIN`
- `REMOVED`

جداکردن Review Status و Publication Status باعث می‌شود مفهوم تأیید محتوا از نتیجه انتشار مستقل باقی بماند.

## 6.3. Transition Rules

- `RECEIVED → SCREENING`
- `SCREENING → PENDING_REVIEW`
- `SCREENING → ESCALATED`
- `PENDING_REVIEW → APPROVED`
- `PENDING_REVIEW → REJECTED`
- `PENDING_REVIEW → NEEDS_EDIT`
- `PENDING_REVIEW → ESCALATED`
- `ESCALATED → APPROVED / REJECTED`
- `APPROVED → QUEUED`
- `QUEUED → PUBLISHING`
- `PUBLISHING → PUBLISHED / FAILED / UNCERTAIN`

انصراف کاربر تنها در وضعیت‌های مجاز قبل از انتشار پذیرفته شود.

برای `UNCERTAIN` باید مسیر تطبیق و بررسی انسانی وجود داشته باشد تا از انتشار دوباره جلوگیری شود.

---

# 7. Database Design

## 7.1. Entities

### users

| Field | Type |
|---|---|
| id | UUID, PK |
| telegram_user_id | BIGINT, UNIQUE |
| status | ENUM |
| accepted_policy_version | VARCHAR, nullable |
| accepted_at | TIMESTAMPTZ, nullable |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

### submissions

| Field | Type |
|---|---|
| id | UUID, PK |
| public_code | VARCHAR, UNIQUE |
| user_id | UUID, FK |
| original_text | TEXT |
| normalized_text | TEXT |
| review_status | ENUM |
| publication_status | ENUM |
| source_update_id | BIGINT |
| source_message_id | BIGINT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

### moderation_results

| Field | Type |
|---|---|
| id | UUID, PK |
| submission_id | UUID, FK |
| risk_level | ENUM |
| categories | JSONB |
| explanation | TEXT |
| engine | VARCHAR |
| engine_version | VARCHAR |
| status | ENUM |
| created_at | TIMESTAMPTZ |

### admin_accounts

| Field | Type |
|---|---|
| id | UUID, PK |
| telegram_user_id | BIGINT, UNIQUE |
| role | ENUM |
| is_active | BOOLEAN |
| created_at | TIMESTAMPTZ |

### admin_reviews

| Field | Type |
|---|---|
| id | UUID, PK |
| submission_id | UUID, FK |
| admin_id | UUID, FK |
| decision | ENUM |
| reason_code | VARCHAR |
| note | TEXT |
| created_at | TIMESTAMPTZ |

### publications

| Field | Type |
|---|---|
| id | UUID, PK |
| submission_id | UUID, FK |
| channel_id | BIGINT |
| telegram_message_id | BIGINT, nullable |
| attempt_status | ENUM |
| attempt_count | INTEGER |
| published_at | TIMESTAMPTZ, nullable |
| created_at | TIMESTAMPTZ |

### restrictions

| Field | Type |
|---|---|
| id | UUID, PK |
| user_id | UUID, FK |
| type | ENUM |
| reason | TEXT |
| created_by | UUID, FK |
| expires_at | TIMESTAMPTZ, nullable |
| created_at | TIMESTAMPTZ |

### audit_logs

| Field | Type |
|---|---|
| id | UUID, PK |
| actor_admin_id | UUID, nullable |
| action | VARCHAR |
| target_type | VARCHAR |
| target_id | UUID |
| metadata | JSONB |
| created_at | TIMESTAMPTZ |

### processed_updates

| Field | Type |
|---|---|
| update_id | BIGINT, PK |
| processed_at | TIMESTAMPTZ |

برای سیاست نگهداری اطلاعات، فیلدهای لازم مانند زمان انقضا، زمان حذف منطقی یا زمان حذف واقعی نیز باید در مهاجرت‌های مرتبط اضافه شوند.

## 7.2. Database Constraints

- User ID باید Unique باشد.
- Public Code باید Unique و غیرقابل حدس باشد.
- Source Update ID باید از پردازش تکراری جلوگیری کند.
- Submission باید دقیقاً به یک User تعلق داشته باشد.
- هر تصمیم مدیریتی باید Actor مشخص داشته باشد.
- وضعیت انتشار باید با رکورد انتشار سازگار باشد.
- تنها یک Publication فعال برای هر Submission و Channel مجاز باشد.
- ایندکس برای وضعیت بررسی، تاریخ ایجاد و شناسه فرستنده تعریف شود.

## 7.3. Transactions

عملیات‌های زیر باید اتمیک باشند:

- ثبت پیام و ثبت رویداد داخلی
- تأیید پیام و تغییر وضعیت
- ثبت محدودیت کاربر و Audit Log
- ثبت تصمیم ادمین و تغییر وضعیت پیام

در عملیات انتشار خارجی، تراکنش دیتابیس نباید در تمام مدت انتظار پاسخ Telegram باز بماند.

---

# 8. Telegram Bot Interface

## 8.1. User Commands

| Command | Action |
|---|---|
| `/start` | شروع، معرفی و پذیرش قوانین |
| `/help` | راهنما |
| `/rules` | قوانین کانال |
| `/privacy` | سیاست داده و حریم خصوصی |
| `/submit` | راهنمای ارسال پیام |
| `/my_messages` | فهرست پیام‌های کاربر |
| `/cancel` | لغو عملیات جاری |
| `/delete` | ثبت درخواست حذف داده یا پیام |

## 8.2. Admin Commands

| Command | Action |
|---|---|
| `/admin` | منوی مدیریت |
| `/pending` | پیام‌های در انتظار |
| `/review` | بررسی پیام مشخص |
| `/stats` | آمار پایه |
| `/restrictions` | مدیریت محدودیت‌ها |
| `/audit` | لاگ‌های مجاز |

## 8.3. Inline Actions

برای بررسی پیام:

- Approve
- Reject
- Escalate
- Next
- Previous

دکمه‌های حساس باید در سرور مجوزسنجی شوند و نباید حاوی شناسه یا اطلاعات شخصی کاربران باشند.

## 8.4. Callback Security

- Callback Data فقط شامل شناسه کوتاه عملیات باشد.
- وضعیت فعلی پیام از دیتابیس خوانده شود.
- نقش ادمین در هر درخواست مجدداً بررسی شود.
- استفاده چندباره از Callback نباید منجر به چندبار اجرا شدن عملیات شود.
- نتیجه عملیات باید به ادمین نمایش داده شود.

---

# 9. Anti-Spam System

## 9.1. Rate Limits

مقادیر اولیه پیشنهادی:

- حداکثر ۳ پیام در ساعت برای هر کاربر.
- حداقل ۳۰ ثانیه فاصله بین دو ارسال.
- حداکثر ۱۰ پیام در روز.
- محدودیت جداگانه برای کاربران دارای سابقه تخلف.

تمام مقادیر باید از Configuration قابل تنظیم باشند.

## 9.2. Duplicate Detection

تشخیص تکرار بر اساس:

- Hash متن نرمال‌شده
- مقایسه متن‌های اخیر همان کاربر
- تشخیص ارسال یکسان در بازه زمانی کوتاه

در MVP استفاده از Hash و مقایسه قطعی کافی است.

تشخیص شباهت معنایی به نسخه بعد منتقل شود.

## 9.3. Abuse Handling

برای کاربران متخلف:

- Warning
- Temporary Restriction
- Permanent Restriction
- Manual Review

محدودیت خودکار بلندمدت نباید صرفاً بر اساس خروجی غیرقطعی AI اعمال شود.

---

# 10. AI Moderation Adapter

## 10.1. Requirements

سیستم AI باید مستقل از Provider پیاده‌سازی شود.

رابط مفهومی:

`ModerationProvider.evaluate(text, context) -> ModerationResult`

هدف:

- امکان جایگزینی Provider
- امکان غیرفعال‌سازی AI
- امکان تست بدون API واقعی
- امکان ثبت عملکرد مدل‌های مختلف

## 10.2. Input Privacy

- Telegram User ID نباید به‌صورت پیش‌فرض برای مدل ارسال شود.
- متن ارسالی باید از داده‌های غیرضروری پاک‌سازی شود.
- اطلاعات حساس شناسایی‌شده در صورت امکان Mask شوند.
- استفاده از سرویس خارجی باید در سیاست حریم خصوصی اعلام شود.
- هیچ متن خصوصی نباید در لاگ خام HTTP ثبت شود.

## 10.3. AI Output

خروجی باید ساختاریافته و اعتبارسنجی شود:

- `categories`
- `risk_level`
- `reason`
- `requires_human_review`
- `confidence` در صورت پشتیبانی و کالیبره‌بودن مدل

Confidence مدل نباید به‌تنهایی معادل احتمال واقعی درست‌بودن تصمیم در نظر گرفته شود.

## 10.4. Failure Policy

اگر Provider پاسخ ندهد:

1. خطا ثبت شود.
2. پیام از بین نرود.
3. وضعیت بررسی خودکار به `FAILED` منتقل شود.
4. پیام برای بررسی دستی ارسال شود.
5. انتشار خودکار انجام نشود.

---

# 11. Security Requirements

## 11.1. Authentication

- دسترسی ادمین از طریق Telegram User ID و لیست مجوزهای ذخیره‌شده در دیتابیس تعیین شود.
- تنها Owner مجاز به تغییر نقش‌های مدیریتی باشد.
- شناسه‌های مدیریتی نباید از متن پیام استخراج شوند.

## 11.2. Authorization

تمام عملیات باید بر اساس اصل Least Privilege اجرا شوند.

محدودیت دسترسی به اطلاعات هویتی باید در Application Service اعمال شود، نه فقط با مخفی‌کردن دکمه‌های رابط کاربری.

## 11.3. Data Protection

- اتصال به PostgreSQL با اعتبارنامه محدود.
- عدم قراردادن رمزها در سورس‌کد.
- رمزگذاری Backupها.
- کنترل دسترسی به فایل‌های Log.
- نگهداری Token ربات در Secret/Environment.
- رمزگذاری داده‌های حساس در صورت نیاز مطابق Threat Model.
- ثبت عملیات دسترسی به هویت کاربران.

## 11.4. Privacy Requirements

قبل از اولین ارسال، کاربر باید بداند:

1. پیام او برای مخاطبان کانال ناشناس خواهد بود.
2. شناسه عددی تلگرام او توسط سیستم ذخیره می‌شود.
3. دسترسی به این شناسه محدود است.
4. پیام ممکن است توسط ادمین و سرویس پردازش محتوا بررسی شود.
5. اطلاعات چه مدت نگهداری می‌شوند.
6. چه روش‌هایی برای درخواست حذف اطلاعات وجود دارد.

### Default Retention Policy

پیشنهاد اولیه برای بررسی حقوقی و محصولی:

- پیام‌های ردشده: حذف محتوای اصلی پس از ۳۰ روز.
- پیام‌های منتشرنشده: حذف داده اضافی پس از ۳۰ روز از بسته‌شدن پرونده.
- ارتباط هویت و پیام منتشرشده: نگهداری محدود، با پیش‌فرض ۹۰ روز.
- موارد دارای گزارش تخلف: نگهداری تا پایان بررسی و دوره مشخص بعد از آن.
- Audit Logs: زمان نگهداری مشخص بر اساس سطح حساسیت و ضرورت امنیتی.

این مقادیر نهایی نیستند و باید متناسب با قوانین قابل اعمال و سیاست اعلام‌شده به کاربران تصویب شوند.

اطلاعات Backup نیز باید سیاست انقضا و حذف مشخص داشته باشند.

---

# 12. Project Structure

ساختار پیشنهادی:

```text
anonymous-confession-bot/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── compose.yaml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database.md
│   ├── moderation-policy.md
│   ├── security.md
│   └── deployment.md
│
├── src/
│   └── confession_bot/
│       ├── main.py
│       ├── config.py
│       │
│       ├── domain/
│       │   ├── entities/
│       │   ├── enums/
│       │   ├── exceptions/
│       │   └── policies/
│       │
│       ├── application/
│       │   ├── services/
│       │   ├── use_cases/
│       │   ├── interfaces/
│       │   └── dto/
│       │
│       ├── infrastructure/
│       │   ├── database/
│       │   │   ├── models/
│       │   │   └── repositories/
│       │   ├── telegram/
│       │   ├── moderation/
│       │   ├── security/
│       │   └── logging/
│       │
│       ├── presentation/
│       │   └── telegram/
│       │       ├── handlers/
│       │       ├── keyboards/
│       │       ├── middlewares/
│       │       └── filters/
│       │
│       └── workers/
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── e2e/
│
└── scripts/
```

توضیحات:

- `domain`: قوانین اصلی کسب‌وکار.
- `application`: پیاده‌سازی Use Caseها.
- `infrastructure`: ارتباط با دیتابیس، تلگرام و AI.
- `presentation`: دریافت ورودی‌ها و نمایش خروجی‌ها.
- `workers`: اجرای وظایف پس‌زمینه، در صورت نیاز.
- `tests`: تست‌های خودکار در سطوح مختلف.

این ساختار یک پیشنهاد اولیه است؛ برای ماژول‌های کوچک می‌توان از فایل‌های کمتر استفاده کرد.

---

# 13. Configuration

متغیرهای محیطی پیشنهادی:

```dotenv
APP_ENV=development
LOG_LEVEL=INFO

BOT_TOKEN=
CHANNEL_ID=
OWNER_TELEGRAM_ID=

DATABASE_URL=

AI_MODERATION_ENABLED=false
AI_PROVIDER=
AI_MODEL=
AI_API_KEY=

MAX_MESSAGE_LENGTH=2000
MIN_MESSAGE_LENGTH=5

RATE_LIMIT_HOURLY=3
RATE_LIMIT_DAILY=10
MESSAGE_COOLDOWN_SECONDS=30

REQUIRE_MANUAL_APPROVAL=true

WEBHOOK_ENABLED=false
WEBHOOK_URL=
WEBHOOK_SECRET=
```

هیچ مقدار واقعی Token یا Password نباید داخل Git ثبت شود.

فایل `.env.example` فقط باید شامل مقادیر نمونه و بدون اطلاعات حساس باشد.

---

# 14. Testing Strategy

## 14.1. Unit Tests

موارد ضروری:

- نرمال‌سازی فارسی
- اعتبارسنجی پیام
- تعیین وضعیت‌های مجاز
- بررسی محدودیت کاربر
- ارزیابی مجوز ادمین
- محاسبه Rate Limit
- قالب‌بندی پیام منتشرشده
- تبدیل نتیجه AI به مدل داخلی

## 14.2. Integration Tests

- ثبت کاربر در PostgreSQL
- ثبت پیام
- ذخیره نتیجه پالایش
- تغییر وضعیت پیام
- ذخیره تصمیم ادمین
- جلوگیری از عملیات تکراری
- مدیریت خطای تراکنش
- اجرای Migrationها

## 14.3. Security Tests

- تلاش کاربر معمولی برای اجرای Callback ادمین
- استفاده از Callback قدیمی
- تغییر شناسه پیام در درخواست
- دسترسی Moderator به هویت کاربر
- تلاش برای دورزدن Rate Limit
- استخراج داده حساس از Logها
- حمله Prompt Injection در متن ارسالی به AI

## 14.4. End-to-End Tests

سناریوی موفق:

1. کاربر ربات را شروع می‌کند.
2. قوانین را می‌پذیرد.
3. پیام ارسال می‌کند.
4. پیام ثبت می‌شود.
5. سیستم آن را بررسی می‌کند.
6. ادمین تأیید می‌کند.
7. ربات پیام را منتشر می‌کند.
8. لینک انتشار به کاربر نمایش داده می‌شود.

سناریوهای شکست:

- قطع سرویس AI
- قطع موقت PostgreSQL
- عدم دسترسی ربات به کانال
- خطای Telegram API
- دو ادمین با تصمیم هم‌زمان
- دریافت چندباره Update
- مسدودشدن ربات توسط کاربر
- ارسال پیام هنگام رسیدن به محدودیت نرخ
- انصراف قبل از انتشار
- نتیجه نامشخص عملیات انتشار

---

# 15. Deployment Architecture

## 15.1. Development

در محیط توسعه:

- اجرای ربات با Long Polling.
- PostgreSQL داخل Docker.
- استفاده از دیتابیس مستقل توسعه.
- AI Provider اختیاری یا Mock.
- غیرفعال‌بودن انتشار روی کانال اصلی.

## 15.2. Production

در محیط Production:

- اجرای سرویس ربات داخل Docker.
- PostgreSQL با Volume پایدار.
- Restart Policy مناسب.
- Health Check.
- جمع‌آوری Log.
- Backup زمان‌بندی‌شده.
- مدیریت Secretها.
- محدودسازی دسترسی شبکه.
- مانیتورینگ خطا و مصرف منابع.

برای MVP استفاده از Long Polling در Production نیز قابل قبول است، به شرط اجرای فقط یک Poller فعال و مدیریت درست خاموش‌شدن سرویس.

Webhook می‌تواند در آینده یا از ابتدا، در صورت نیاز زیرساختی، انتخاب شود.

## 15.3. Backup

حداقل الزامات:

- Backup منظم PostgreSQL.
- نگهداری نسخه‌های Backup طبق سیاست مصوب.
- رمزگذاری Backup.
- آزمایش دوره‌ای بازیابی.
- مستندسازی فرآیند Restore.

---

# 16. Implementation Roadmap

## Phase 1 — Foundation

وظایف:

- ایجاد Repository
- تنظیم uv و pyproject
- ایجاد ساختار پروژه
- تنظیم Docker
- اتصال PostgreSQL
- تنظیم SQLAlchemy
- ایجاد Alembic
- مدیریت Configuration
- راه‌اندازی Logging
- تنظیم Ruff و pytest

**Deliverable:** پروژه قابل اجرا با زیرساخت پایه.

## Phase 2 — User & Submission

وظایف:

- پیاده‌سازی User Entity
- پیاده‌سازی Submission Entity
- تعریف Repository Interface
- پیاده‌سازی دستورات کاربر
- پذیرش قوانین
- دریافت و اعتبارسنجی پیام
- ثبت پیام
- تولید کد پیگیری
- جلوگیری از ثبت تکراری

**Deliverable:** دریافت و ثبت امن پیام.

## Phase 3 — Moderation

وظایف:

- نرمال‌سازی فارسی
- فیلتر الگوهای ممنوعه
- تشخیص اطلاعات حساس
- تعریف ModerationResult
- ایجاد AI Adapter
- مدیریت Timeout
- ثبت نتایج پالایش
- پیاده‌سازی انتقال وضعیت‌ها

**Deliverable:** سیستم ارزیابی محتوای قابل تست.

## Phase 4 — Admin Workflow

وظایف:

- تعریف نقش‌ها
- پیاده‌سازی Permission Policy
- ایجاد پنل تلگرامی
- نمایش صف بررسی
- دکمه‌های Approve / Reject
- ثبت دلیل رد
- ارجاع موارد حساس
- ثبت Audit Log

**Deliverable:** فرآیند کامل مدیریت پیام‌ها.

## Phase 5 — Publishing

وظایف:

- ایجاد Publisher Service
- طراحی قالب انتشار
- مدیریت انتشار امن
- ثبت Channel Message ID
- مدیریت خطاها
- جلوگیری از انتشار تکراری
- اطلاع‌رسانی به کاربر

**Deliverable:** چرخه کامل دریافت تا انتشار.

## Phase 6 — Security & Hardening

وظایف:

- پیاده‌سازی Rate Limiting
- شناسایی پیام‌های تکراری
- محدودیت کاربران متخلف
- بررسی امنیت Callbackها
- پیاده‌سازی سیاست حذف و نگهداری
- افزایش پوشش تست‌ها
- تست بازیابی دیتابیس
- بررسی مدیریت Secretها

**Deliverable:** نسخه آماده انتشار محدود.

## Phase 7 — Production Release

وظایف:

- ساخت Image نهایی
- تنظیم محیط Production
- آماده‌سازی کانال
- بررسی Permissionهای ربات
- اجرای Migration
- بررسی Health Check
- اجرای Smoke Test
- فعال‌سازی Monitoring
- مستندسازی راه‌اندازی و بازیابی

**Deliverable:** نسخه عملیاتی MVP.

---

# 17. Acceptance Criteria

سیستم در صورتی آماده انتشار MVP محسوب می‌شود که:

- کاربران بتوانند پیام متنی ثبت کنند.
- بدون پذیرش قوانین، پیام ثبت نشود.
- تمام پیام‌های معتبر دارای شناسه پیگیری باشند.
- ارتباط پیام و فرستنده در دیتابیس ثبت شود.
- پیام برای مخاطبان کانال ناشناس منتشر شود.
- تمام پیام‌ها قبل از انتشار بررسی انسانی شوند.
- ادمین بدون مجوز نتواند عملیات حساس انجام دهد.
- Moderator نتواند شناسه واقعی فرستنده را بازیابی کند.
- پیام ردشده منتشر نشود.
- پیام تأییدشده بتواند در کانال منتشر شود.
- عملیات تکراری باعث تغییر وضعیت نامعتبر نشود.
- Rate Limit اعمال شود.
- قطع AI باعث ازبین‌رفتن پیام نشود.
- عملیات حساس مدیریتی Audit شوند.
- بازیابی داده از Backup آزمایش شده باشد.
- تست‌های اصلی با موفقیت اجرا شوند.
- خطاهای زیرساختی در Log ثبت شوند، بدون نمایش اطلاعات حساس.
- عملیات حذف داده با سیاست نگهداری سازگار باشد.

---

# 18. Engineering Guidelines

قوانین توسعه پروژه:

1. از Type Hint استفاده شود.
2. منطق کسب‌وکار داخل Telegram Handler نوشته نشود.
3. دسترسی دیتابیس از طریق Repository انجام شود.
4. توابع و کلاس‌ها مسئولیت مشخص داشته باشند.
5. خطاهای دامنه تعریف و مدیریت شوند.
6. کد Async در بخش‌های I/O محور استفاده شود.
7. هیچ وابستگی غیرضروری اضافه نشود.
8. هیچ Token یا Secret در Repository قرار نگیرد.
9. Migration دیتابیس همراه تغییرات Schema نوشته شود.
10. قابلیت‌های اصلی با تست پوشش داده شوند.
11. عملیات حساس Idempotent طراحی شوند.
12. درخواست‌های خارجی Timeout مشخص داشته باشند.
13. ورودی‌های AI غیرقابل اعتماد در نظر گرفته شوند.
14. SQL خام تنها در موارد موجه و با پارامترهای امن استفاده شود.
15. تمام Timestampها در دیتابیس به UTC ذخیره شوند.
16. داده هویتی در خروجی عمومی یا Log معمولی منتشر نشود.
17. قبل از تغییرات بزرگ معماری، مستندات مربوطه به‌روزرسانی شوند.

---

# 19. Future Extensions

پس از تکمیل MVP:

### Version 1.1

- داشبورد آمار پایه
- زمان‌بندی انتشار
- بهبود تشخیص پیام تکراری
- گزارش محتوای منتشرشده
- مدیریت بهتر اعتراض‌ها
- قابلیت ویرایش و ارسال مجدد توسط کاربر

### Version 1.2

- پنل مدیریت تحت وب
- جست‌وجوی پیشرفته
- سیستم پاسخ ناشناس با محافظت در برابر مزاحمت
- دسته‌بندی پیام‌ها
- گزارش‌های عملکرد مدل AI
- ابزار تنظیم قوانین پالایش

### Version 2.0

- مدیریت چند کانال
- Workerهای مستقل
- سیستم Queue پیشرفته
- تحلیل محتوای چندرسانه‌ای
- ارزیابی خودکار کیفیت مدل‌های پالایش
- معماری قابل توسعه برای حجم بالاتر پیام

---

# 20. Unresolved Design Decisions

موارد زیر باید قبل از نهایی‌شدن معماری و پیاده‌سازی مشخص شوند:

1. نام نهایی ربات و کانال.
2. مخاطب عمومی یا محدود به یک جامعه مشخص.
3. تعداد ادمین‌ها.
4. سیاست دقیق دسترسی به هویت فرستنده.
5. شرایط مجاز برای افشای هویت در پنل ادمین.
6. مدت نگهداری داده‌های شخصی.
7. انتخاب AI Provider و سیاست ارسال داده به آن.
8. بودجه پردازش AI.
9. امکان ویرایش پیام توسط ادمین یا فقط توسط فرستنده.
10. نحوه رسیدگی به پیام‌های دارای اطلاعات شخص ثالث.
11. قالب نهایی انتشار.
12. سیاست رسیدگی به اعتراض و گزارش تخلف.
13. انتخاب Long Polling یا Webhook در Production.
14. ظرفیت مورد انتظار پیام‌ها در روز.
15. نیاز یا عدم نیاز به صف انتشار زمان‌بندی‌شده.

---

# 21. Definition of Done

یک قابلیت زمانی تکمیل‌شده در نظر گرفته می‌شود که:

- رفتار مورد انتظار آن مستند شده باشد.
- پیاده‌سازی آن مطابق معماری پروژه باشد.
- تست‌های مرتبط نوشته شده باشند.
- سناریوهای خطا مدیریت شده باشند.
- مجوزهای لازم بررسی شده باشند.
- داده‌های حساس به‌درستی محافظت شوند.
- تغییرات دیتابیس Migration داشته باشند.
- راه‌اندازی و استفاده از قابلیت مستند شده باشد.
- تست‌ها و بررسی‌های کیفیت کد موفق باشند.

**هدف نهایی:** ساخت یک ربات ناشناس قابل اعتماد، امن، قابل نگهداری و توسعه‌پذیر که انتشار پیام‌ها را ساده کند، بدون آنکه ناشناس‌بودن عمومی کاربران به معنی نبود نظارت و کنترل سوءاستفاده باشد.
