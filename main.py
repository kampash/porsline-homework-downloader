import os
import re
import json
import mimetypes
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote

# Load private settings from .env
load_dotenv()

# --------------------------------------------------
# Settings
# --------------------------------------------------
SURVEY_ID = os.getenv("PORSLINE_SURVEY_ID", "").strip()
API_KEY = os.getenv("PORSLINE_API_KEY", "").strip()

DOWNLOAD_DIR = "homework_downloads"
RESULTS_FILE = "results_v2.json"

API_BASE = "https://survey.porsline.ir"
TABLE_URL = f"{API_BASE}/api/v2/surveys/{SURVEY_ID}/responses/results-table/"

API_HEADERS = {
    "Authorization": f"API-Key {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def normalize_digits(value):
    """Convert Persian and Arabic digits to English digits."""
    if value is None:
        return ""
    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )
    return str(value).translate(table)


def sanitize(value):
    if value is None:
        return ""
    value = normalize_digits(value)
    value = re.sub(r'[\\/*?:"<>|]', "", str(value))
    value = re.sub(r"\s+", "_", value.strip())
    return value.strip("._")


def get_title_map(headers):
    """Map both column IDs and positions to column titles."""
    result = {}
    for index, column in enumerate(headers):
        if not isinstance(column, dict):
            continue
        title = str(column.get("title") or f"column_{index}").strip()
        result[index] = title
        if column.get("id") is not None:
            result[str(column["id"])] = title
    return result


def get_rows(data):
    for key in ("body", "rows", "data", "results", "records"):
        value = data.get(key)
        if isinstance(value, list):
            print(f"Rows found in '{key}'.")
            return value
    return []


def fetch_survey_data():
    """Fetch the response table directly from Porsline."""
    if not SURVEY_ID:
        raise RuntimeError("ابتدا PORSLINE_SURVEY_ID را در فایل .env وارد کنید.")
    if not API_KEY:
        raise RuntimeError("ابتدا PORSLINE_API_KEY را در فایل .env وارد کنید.")

    response = requests.get(TABLE_URL, headers=API_HEADERS, timeout=60)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("پاسخ پرس‌لاین در قالب JSON مورد انتظار نیست.")

    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return data


def row_cells(row):
    """Return cells and their corresponding column titles."""
    if isinstance(row, dict):
        cells = row.get("data")
        if isinstance(cells, list):
            return [(i, value) for i, value in enumerate(cells)]

        # Some table responses store values directly under column IDs.
        ignored = {"id", "data", "created_at", "updated_at"}
        return [(key, value) for key, value in row.items() if key not in ignored]

    if isinstance(row, list):
        return list(enumerate(row))

    return []


def find_column_index(headers, patterns):
    for index, column in enumerate(headers):
        if not isinstance(column, dict):
            continue
        title = str(column.get("title", "")).strip().lower()
        if any(pattern in title for pattern in patterns):
            return index
    return None


def get_cell_value(cells, index):
    if index is None:
        return ""
    if index < len(cells):
        return cells[index]
    return ""


def value_to_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def collect_file_objects(value):
    """Recursively find attachment objects and direct URLs."""
    found = []

    def walk(item):
        if isinstance(item, dict):
            # An attachment may contain a key, a URL, or both.
            if item.get("key") or item.get("url") or item.get("download_url"):
                found.append(item)
                return
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str) and item.strip().lower().startswith(("http://", "https://")):
            found.append({"url": item.strip()})

    walk(value)

    # Remove duplicate attachments.
    unique = []
    seen = set()
    for item in found:
        marker = item.get("key") or item.get("url") or item.get("download_url")
        if marker and marker not in seen:
            seen.add(marker)
            unique.append(item)
    return unique


def file_endpoint_from_key(file_key):
    """
    Porsline file key is expected in the form:
    survey_hash/response_id/question_id
    """
    parts = str(file_key).strip().strip("/").split("/")
    if len(parts) != 3:
        return None

    survey_hash, response_id, question_id = parts
    return (
        f"{API_BASE}/api/surveys/{survey_hash}/files/"
        f"{question_id}-{response_id}/"
    )


def extract_download_url(response):
    """Extract a storage URL from common Porsline API response formats."""
    # Redirects are followed by requests; check the final URL first.
    final_url = response.url
    if final_url.startswith("http") and "survey.porsline.ir/api/" not in final_url:
        return final_url

    content_type = response.headers.get("Content-Type", "").lower()
    text = response.text.strip()

    if "json" in content_type or text.startswith(("{", "[")):
        try:
            payload = response.json()
            if isinstance(payload, str):
                return payload.strip()
            if isinstance(payload, dict):
                for key in ("url", "download_url", "file_url", "signed_url"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.startswith("http"):
                        return value
                # Some APIs wrap the URL in a nested object.
                for value in payload.values():
                    if isinstance(value, dict):
                        for key in ("url", "download_url", "file_url", "signed_url"):
                            nested = value.get(key)
                            if isinstance(nested, str) and nested.startswith("http"):
                                return nested
        except (ValueError, TypeError):
            pass

    text = text.strip('"').strip("'")
    if text.startswith("http://") or text.startswith("https://"):
        return text

    return None


def guess_extension(attachment, download_response=None):
    name = attachment.get("name") or attachment.get("filename")
    if name:
        ext = os.path.splitext(str(name))[1]
        if ext:
            return ext

    if download_response is not None:
        content_type = download_response.headers.get("Content-Type", "").split(";")[0].strip()
        ext = mimetypes.guess_extension(content_type) if content_type else None
        if ext:
            return ext

    return ".file"


def save_response_content(response, path):
    response.raise_for_status()
    # Avoid saving an HTML/JSON error page as if it were an attachment.
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" in content_type:
        raise ValueError("سرور به‌جای فایل، صفحه HTML برگردانده است.")
    with open(path, "wb") as file:
        for chunk in response.iter_content(chunk_size=16384):
            if chunk:
                file.write(chunk)
    return os.path.getsize(path)


def download_attachment(attachment, filename):
    """Download either a direct attachment URL or a Porsline file key."""
    direct_url = attachment.get("url") or attachment.get("download_url")
    file_key = attachment.get("key")

    if direct_url and str(direct_url).startswith(("http://", "https://")):
        response = requests.get(str(direct_url), stream=True, timeout=90)
        response.raise_for_status()

        # If the direct URL is an API endpoint returning a storage URL,
        # resolve it before downloading the actual file.
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type or (
            not response.headers.get("Content-Disposition")
            and response.url.startswith(API_BASE)
            and "text/" in content_type
        ):
            storage_url = extract_download_url(response)
            response.close()
            if storage_url and storage_url != direct_url:
                response = requests.get(storage_url, stream=True, timeout=90)
                size = save_response_content(response, filename)
                response.close()
                return size

        size = save_response_content(response, filename)
        response.close()
        return size

    if not file_key:
        raise ValueError("پیوست نه URL دارد و نه key.")

    endpoint = file_endpoint_from_key(file_key)
    if not endpoint:
        raise ValueError(f"ساختار کلید فایل قابل تشخیص نیست: {file_key}")

    # First request: authenticated Porsline API to obtain the storage URL.
    response = requests.get(endpoint, headers=API_HEADERS, timeout=60)
    response.raise_for_status()

    storage_url = extract_download_url(response)

    # Some API responses may return the file bytes directly.
    if not storage_url:
        size = save_response_content(response, filename)
        response.close()
        return size

    response.close()

    # Second request: download from storage without Porsline Authorization.
    storage_response = requests.get(storage_url, stream=True, timeout=90)
    size = save_response_content(storage_response, filename)
    storage_response.close()
    return size


def main():
    try:
        data = fetch_survey_data()
    except Exception as error:
        print(f"❌ دریافت اطلاعات پرسشنامه ناموفق بود: {error}")
        return

    headers = data.get("header", [])
    rows = get_rows(data)

    if not rows:
        print("❌ هیچ ردیفی در پاسخ پرس‌لاین پیدا نشد.")
        print("کلیدهای موجود:", list(data.keys()))
        return

    title_map = get_title_map(headers)

    grade_idx = find_column_index(headers, ("پایه تحصیلی", "پایه"))
    first_idx = None
    last_idx = None
    for index, column in enumerate(headers):
        if not isinstance(column, dict):
            continue
        title = str(column.get("title", "")).strip()
        normalized_title = title.replace("‌", " ")
        if last_idx is None and "نام خانوادگی" in normalized_title:
            last_idx = index
        elif first_idx is None and (
            title.startswith("نام:") or normalized_title == "نام"
        ):
            first_idx = index
    date_idx = find_column_index(headers, ("تاریخ",))
    file_indices = [
        index for index, column in enumerate(headers)
        if isinstance(column, dict)
        and (
            str(column.get("type", "")).lower() == "file"
            or "فایل" in str(column.get("title", ""))
            or "پیوست" in str(column.get("title", ""))
        )
    ]

    print(f"\n📊 تعداد پاسخ‌ها: {len(rows)}")
    print("📥 شروع دریافت پیوست‌ها...\n")

    downloaded = 0
    failed = 0
    no_file = 0

    for row_number, row in enumerate(rows, start=1):
        pairs = row_cells(row)
        cells = [value for _, value in pairs]

        grade = value_to_text(get_cell_value(cells, grade_idx))
        first_name = value_to_text(get_cell_value(cells, first_idx))
        last_name = value_to_text(get_cell_value(cells, last_idx))
        date_value = value_to_text(get_cell_value(cells, date_idx))
        date_digits = re.sub(r"\D", "", normalize_digits(date_value))

        name_parts = [sanitize(x) for x in (grade, first_name, last_name, date_digits) if sanitize(x)]
        student_name = "_".join(name_parts) or f"student_{row_number}"

        attachments = []
        # Prefer columns identified as file/attachment columns.
        for file_index in file_indices:
            if file_index < len(cells):
                attachments.extend(collect_file_objects(cells[file_index]))

        # Fallback: scan all cells, in case the API omitted the file type.
        if not attachments:
            for value in cells:
                attachments.extend(collect_file_objects(value))

        # Deduplicate after combining columns.
        unique_attachments = []
        seen = set()
        for attachment in attachments:
            marker = attachment.get("key") or attachment.get("url") or attachment.get("download_url")
            if marker and marker not in seen:
                seen.add(marker)
                unique_attachments.append(attachment)
        attachments = unique_attachments

        print(f"[{row_number}/{len(rows)}] {student_name}")

        if not attachments:
            print("   ℹ️ پیوستی برای این پاسخ پیدا نشد.")
            no_file += 1
            continue

        for file_number, attachment in enumerate(attachments, start=1):
            original_name = attachment.get("name") or attachment.get("filename") or ""
            extension = os.path.splitext(str(original_name))[1]
            if not extension:
                extension = ".file"

            suffix = f"_{file_number}" if len(attachments) > 1 else ""
            filename = f"{student_name}{suffix}{extension}"
            target_path = os.path.join(DOWNLOAD_DIR, filename)

            # Avoid overwriting a previous file with the same name.
            base, ext = os.path.splitext(target_path)
            counter = 2
            while os.path.exists(target_path):
                target_path = f"{base}_{counter}{ext}"
                counter += 1

            try:
                size = download_attachment(attachment, target_path)
                print(f"   ✅ ذخیره شد: {os.path.basename(target_path)} ({size / 1024:.1f} KB)")
                downloaded += 1
            except Exception as error:
                print(f"   ❌ دانلود ناموفق بود: {error}")
                failed += 1
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except OSError:
                        pass

    print("\n" + "=" * 55)
    print("پایان عملیات")
    print(f"تعداد پاسخ‌ها: {len(rows)}")
    print(f"فایل‌های دانلودشده: {downloaded}")
    print(f"پاسخ‌های بدون پیوست: {no_file}")
    print(f"دانلودهای ناموفق: {failed}")
    print(f"مسیر ذخیره فایل‌ها: {os.path.abspath(DOWNLOAD_DIR)}")


if __name__ == "__main__":
    main()
