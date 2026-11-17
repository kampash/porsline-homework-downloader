# Porsline Homework Downloader

ابزاری با پایتون برای دریافت و مرتب‌سازی فایل‌های تکالیف ارسالی شاگردان از طریق پرس‌لاین.

A Python tool to download and organize student homework attachments submitted through Porsline.

---

## فارسی

### معرفی

این برنامه با استفاده از API پرس‌لاین، پاسخ‌های یک پرسشنامه را دریافت می‌کند، فایل‌های پیوست‌شده به پاسخ‌ها را پیدا می‌کند و آن‌ها را در رایانه ذخیره می‌کند.

نام فایل‌های دانلودشده، در صورت وجود اطلاعات مربوط، بر اساس پایه تحصیلی، نام، نام خانوادگی و تاریخ پاسخ ساخته می‌شود. اگر فایلی با همان نام از قبل وجود داشته باشد، برنامه نام دیگری برای فایل جدید انتخاب می‌کند تا فایل قبلی بازنویسی نشود.

### امکانات فعلی

- دریافت داده‌های جدول پاسخ‌های پرسشنامه از API پرس‌لاین
- شناسایی پیوست‌ها از طریق URL مستقیم یا کلید فایل (File Key)
- دانلود پیوست‌ها
- ساخت نام فایل بر اساس اطلاعات شاگرد و تاریخ پاسخ
- جلوگیری از بازنویسی فایل‌های هم‌نام
- نمایش گزارش تعداد دانلودهای موفق، ناموفق و پاسخ‌های بدون پیوست
- ذخیره پاسخ خام API در فایل `results_v2.json`

### پیش‌نیازها

- Python 3.9 یا جدیدتر
- کلید API معتبر پرس‌لاین
- شناسه پرسشنامه (Survey ID)
- دسترسی اینترنت

### نصب و راه‌اندازی

۱. مخزن را دریافت یا Clone کنید:

```bash
git clone https://github.com/kampash/porsline-homework-downloader.git
cd porsline-homework-downloader
```

۲. وابستگی‌ها را نصب کنید:

```bash
python -m pip install -r requirements.txt
```

۳. از فایل نمونه، یک کپی با نام `.env` بسازید:

در Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

در macOS یا Linux:

```bash
cp .env.example .env
```

۴. فایل `.env` را باز کنید و شناسه پرسشنامه و کلید API خود را وارد کنید:

```env
PORSline_SURVEY_ID=your_survey_id
PORSLINE_API_KEY=your_api_key
```

**مهم:** فایل `.env` خصوصی است. کلید واقعی API خود را در GitHub منتشر نکنید و آن را برای دیگران ارسال نکنید.

۵. برنامه را اجرا کنید:

```bash
python main.py
```

### محل ذخیره فایل‌ها

- فایل‌های پیوست در پوشه `homework_downloads` ذخیره می‌شوند.
- داده خام پاسخ API در فایل `results_v2.json` ذخیره می‌شود.

این دو مورد در `.gitignore` قرار دارند تا به‌طور تصادفی وارد مخزن Git نشوند.

### نکته درباره دریافت پاسخ‌ها

نسخه فعلی برنامه یک درخواست برای دریافت جدول پاسخ‌ها ارسال می‌کند. اگر API پرس‌لاین پاسخ‌ها را صفحه‌بندی کند، ممکن است همه پاسخ‌ها در این درخواست دریافت نشوند. پشتیبانی از دریافت کامل صفحات باید متناسب با ساختار واقعی پاسخ API بررسی شود.

### حریم خصوصی

فایل‌های تکالیف ممکن است شامل نام، اطلاعات آموزشی یا داده‌های شخصی شاگردان باشند. مسئولیت نگهداری امن این فایل‌ها و رعایت قوانین و مقررات مربوط به حریم خصوصی بر عهده استفاده‌کننده است.

---

## English

### Overview

This tool uses the Porsline API to retrieve a survey response table, identify file attachments, and download those attachments to a local folder.

When available, downloaded filenames are generated from the student's grade, first name, last name, and response date. Existing files are not overwritten; a suffix is added to duplicate filenames.

### Current features

- Fetches a Porsline survey response table through the API
- Finds attachments represented by direct URLs or file keys
- Downloads attachment files
- Generates filenames using student and response information
- Avoids overwriting files with duplicate names
- Reports successful downloads, failed downloads, and responses without attachments
- Saves the raw API response to `results_v2.json`

### Requirements

- Python 3.9 or newer
- A valid Porsline API key
- A Porsline Survey ID
- Internet access

### Installation

1. Clone this repository:

```bash
git clone https://github.com/kampash/porsline-homework-downloader.git
cd porsline-homework-downloader
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`.

4. Add your own Survey ID and API key to `.env`:

```env
PORSline_SURVEY_ID=your_survey_id
PORSLINE_API_KEY=your_api_key
```

5. Run the program:

```bash
python main.py
```

### Output

- Downloaded attachments are saved in `homework_downloads/`.
- The raw API response is saved as `results_v2.json`.

### Privacy and security

Never commit your real `.env` file or share your API key. Downloaded homework and response data may contain personal information. Keep these files secure and use them in accordance with applicable privacy requirements.

### Current limitation

The current version makes one request to retrieve the response table. If the Porsline API paginates the response data, additional work may be required to retrieve every page.

---

## License

A license has not been selected for this repository yet.
