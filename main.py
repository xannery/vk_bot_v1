import re
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from typing import Optional

import gspread
from vkbottle.bot import Bot, Message
from vkbottle import BaseStateGroup, CtxStorage, Keyboard, Text, KeyboardButtonColor
from google.oauth2.service_account import Credentials

from config import TOKEN, CREDENTIALS_FILE, SPREADSHEET_ID, ADMINS

# ================== Google Sheets ==================
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)

sheet_authors = sh.worksheet("Авторы")
sheet_focus = sh.worksheet("Фокус-группа")

# ================== Бот ==================
bot = Bot(token=TOKEN)
storage = CtxStorage()

main_keyboard = (
    Keyboard(one_time=False)
    .add(Text("Рекомендация"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("ФГ"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Другое"), color=KeyboardButtonColor.SECONDARY)
    .get_json()
)


class RecommendState(BaseStateGroup):
    WAITING_LINK = "waiting_link"
    WAITING_THEME = "waiting_theme"


class FocusState(BaseStateGroup):
    FIO = "fio"
    AGE = "age"
    STATUS = "status"
    ABOUT = "about"


ALLOWED_DOMAINS = {
    "vk.com": "vk",
    "vk.ru": "vk",
    "t.me": "telegram",
    "telegram.me": "telegram",
    "instagram.com": "instagram",
    "tiktok.com": "tiktok",
}


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")
    return urlunparse(("https", netloc, path, "", "", ""))


def get_platform(url: str) -> Optional[str]:
    netloc = urlparse(url).netloc.lower().replace("www.", "")
    for domain, name in ALLOWED_DOMAINS.items():
        if domain in netloc:
            return name
    return None


def find_author_row(normalized: str):
    try:
        records = sheet_authors.get_all_records()
        for i, row in enumerate(records, start=2):
            row_normalized = str(row.get("Нормализованная ссылка", "")).strip()
            if row_normalized == normalized:
                return i, row
    except Exception as e:
        print(f"Ошибка при поиске автора: {e}")
    return None, None


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


async def safe_delete_state(peer_id: int):
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        pass


def safe_storage_delete(peer_id: int):
    try:
        storage.delete(peer_id)
    except KeyError:
        pass


@bot.on.private_message()
async def handler(message: Message):
    peer_id = message.peer_id
    text = (message.text or "").strip()
    text_lower = text.lower()

    current_state = await bot.state_dispenser.get(peer_id)
    state_name = str(current_state).lower() if current_state else ""

    # ================== АДМИН КОМАНДЫ ==================
    if text_lower == "/stats" and is_admin(message.from_id):
        authors_count = len(sheet_authors.get_all_records())
        focus_count = len(sheet_focus.get_all_records())
        await message.answer(
            f"Статистика:\nАвторов: {authors_count}\nАнкет фокус-группы: {focus_count}"
        )
        return

    if text_lower == "/export" and is_admin(message.from_id):
        await message.answer(f"Ссылка на таблицу:\n{sh.url}")
        return

    # ================== РЕКОМЕНДАЦИЯ: ЖДЁМ ССЫЛКУ ==================
    if "waiting_link" in state_name:
        urls = re.findall(
            r'https?://[^\s]+|(?:vk\.com|vk\.ru|t\.me|telegram\.me|instagram\.com|tiktok\.com)/[^\s]+',
            text, re.IGNORECASE
        )

        if not urls:
            await message.answer("Попробуйте ещё раз")
            return

        url = urls[0]
        normalized = normalize_url(url)
        platform = get_platform(normalized)

        if not platform:
            await message.answer("Попробуйте ещё раз")
            return

        storage.set(peer_id, {
            "url": url,
            "normalized": normalized,
            "platform": platform
        })

        await bot.state_dispenser.set(peer_id, RecommendState.WAITING_THEME)
        await message.answer("Как бы Вы могли описать деятельность автора? (до 50 символов)")
        return

    # ================== РЕКОМЕНДАЦИЯ: ЖДЁМ ТЕМАТИКУ ==================
    if "waiting_theme" in state_name:
        theme = text.strip()

        if len(theme) > 50:
            await message.answer("Слишком длинно. Опишите деятельность автора до 50 символов.")
            return

        if not theme:
            await message.answer("Напишите хотя бы короткое описание.")
            return

        data = storage.get(peer_id)
        if not data:
            await bot.state_dispenser.set(peer_id, RecommendState.WAITING_LINK)
            await message.answer("Что-то пошло не так. Пришлите ссылку заново.")
            return

        url = data["url"]
        normalized = data["normalized"]
        platform = data["platform"]

        row_num, existing = find_author_row(normalized)

        if existing:
            # Обновляем существующего автора
            old_themes = str(existing.get("Тематики", "") or "")
            themes = set(map(str.strip, old_themes.split(",")))
            themes.discard("")
            themes.add(theme)
            new_themes = ", ".join(sorted(themes))

            try:
                mentions = int(existing.get("Кол-во упоминаний", 1)) + 1
            except (ValueError, TypeError):
                mentions = 2

            # D = Тематики, E = Кол-во упоминаний, F = Дата первого добавления
            sheet_authors.update(f"D{row_num}:F{row_num}", [[
                new_themes,
                mentions,
                existing.get("Дата первого добавления", "")
            ]])
        else:
            # Новый автор
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet_authors.append_row([
                url,
                normalized,
                platform,
                theme,
                1,
                now
            ])

        await safe_delete_state(peer_id)
        safe_storage_delete(peer_id)

        await message.answer(
            "Спасибо за рекомендацию! Вы можете дать рекомендацию на автора ещё.",
            keyboard=main_keyboard
        )
        return

    # ================== ФОКУС-ГРУППА ==================
    if "fio" in state_name:
        storage.set(peer_id, {"fio": text})
        await bot.state_dispenser.set(peer_id, FocusState.AGE)
        await message.answer("Сколько тебе лет?")
        return

    if "age" in state_name:
        data = storage.get(peer_id) or {}
        data["age"] = text
        storage.set(peer_id, data)
        await bot.state_dispenser.set(peer_id, FocusState.STATUS)
        await message.answer("Твой статус? (студент / работаю / фриланс / другое)")
        return

    if "status" in state_name:
        data = storage.get(peer_id) or {}
        data["status"] = text
        storage.set(peer_id, data)
        await bot.state_dispenser.set(peer_id, FocusState.ABOUT)
        await message.answer(
            "Расскажи коротко:\n"
            "• Сфера деятельности\n"
            "• О себе\n"
            "• Почему хочешь участвовать в фокус-группе"
        )
        return

    if "about" in state_name:
        data = storage.get(peer_id) or {}
        data["about"] = text

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet_focus.append_row([
            now,
            message.from_id,
            data.get("fio", ""),
            data.get("age", ""),
            data.get("status", ""),
            data.get("about", "")
        ])

        await safe_delete_state(peer_id)
        safe_storage_delete(peer_id)

        await message.answer("Спасибо! Анкета сохранена.", keyboard=main_keyboard)
        return

    # ================== МЕНЮ (нет активного состояния) ==================
    if text_lower in ["/start", "начать", "старт", "меню"]:
        await safe_delete_state(peer_id)
        safe_storage_delete(peer_id)
        await message.answer(
            "Редакция ЯЛОН на связи!\n\nВыберите, что хотите сделать:",
            keyboard=main_keyboard
        )
        return

    if text_lower == "рекомендация":
        await bot.state_dispenser.set(peer_id, RecommendState.WAITING_LINK)
        await message.answer(
            "Отправьте ссылку на личную страницу автора в одной из социальных сетей "
            "(VK, Telegram, Instagram, Tik-Tok)."
        )
        return

    if text_lower in ["фг", "фокус", "анкета"]:
        await bot.state_dispenser.set(peer_id, FocusState.FIO)
        await message.answer("Отлично! Давай заполним анкету.\n\nКак тебя зовут? (ФИО)")
        return

    if text_lower == "другое":
        await safe_delete_state(peer_id)
        safe_storage_delete(peer_id)
        await message.answer(
            "Напишите ваш вопрос — мы ответим в ближайшее время.",
            keyboard=main_keyboard
        )
        return

    # По умолчанию показываем меню
    await message.answer(
        "Редакция ЯЛОН на связи!\n\nВыберите, что хотите сделать:",
        keyboard=main_keyboard
    )


if __name__ == "__main__":
    print("Бот успешно запущен")
    bot.run_forever()