from datetime import datetime
from typing import Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials

from bot.config import CREDENTIALS_FILE, SPREADSHEET_ID


scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)

sheet_authors = sh.worksheet("Авторы")
sheet_focus = sh.worksheet("Фокус-группа")


def find_author_info(normalized: str) -> Tuple[int, Optional[str]]:
    try:
        records = sheet_authors.get_all_records()
        count = 0
        first_date = None

        for row in records:
            row_normalized = str(row.get("Нормализованная ссылка", "")).strip()
            if row_normalized == normalized:
                count += 1
                date_val = row.get("Дата первого упоминания") or row.get("Дата")
                if date_val:
                    if first_date is None or str(date_val) < str(first_date):
                        first_date = date_val

        return count, first_date
    except Exception as e:
        print(f"Ошибка при поиске автора: {e}")
        return 0, None


def add_author_recommendation(url: str, normalized: str, platform: str, theme: str) -> int:
    existing_count, first_date = find_author_info(normalized)
    new_count = existing_count + 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not first_date:
        first_date = now

    sheet_authors.append_row([
        url,
        normalized,
        platform,
        theme,
        new_count,
        first_date,
        now
    ])
    return new_count


def add_focus_response(user_id: int, fio: str, age: str, status: str, about: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_focus.append_row([
        now,
        user_id,
        fio,
        age,
        status,
        about
    ])


def get_stats() -> Tuple[int, int]:
    authors_count = len(sheet_authors.get_all_records())
    focus_count = len(sheet_focus.get_all_records())
    return authors_count, focus_count


def get_spreadsheet_url() -> str:
    return sh.url