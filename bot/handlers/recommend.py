import re
from vkbottle.bot import Message

from bot.keyboards import main_keyboard
from bot.states import RecommendState
from bot.utils.helpers import normalize_url, get_platform
from bot.services import sheets
from bot.handlers.menu import safe_delete_state, safe_storage_delete


async def handle_recommend(message: Message, bot, storage, state_name: str) -> bool:
    peer_id = message.peer_id
    text = (message.text or "").strip()

    # ----- Ждём ссылку -----
    if "waiting_link" in state_name:
        urls = re.findall(
            r'https?://[^\s]+|(?:vk\.com|vk\.ru|t\.me|telegram\.me|instagram\.com|tiktok\.com|twitch\.tv)/[^\s]+',
            text, re.IGNORECASE
        )

        if not urls:
            await message.answer("Попробуйте ещё раз")
            return True

        url = urls[0]
        normalized = normalize_url(url)
        platform = get_platform(normalized)

        if not platform:
            await message.answer("Попробуйте ещё раз")
            return True

        storage.set(peer_id, {
            "url": url,
            "normalized": normalized,
            "platform": platform
        })

        await bot.state_dispenser.set(peer_id, RecommendState.WAITING_THEME)
        await message.answer("Как бы Вы могли описать деятельность предлагаемого автора? (до 50 символов)")
        return True

    # ----- Ждём тематику -----
    if "waiting_theme" in state_name:
        theme = text.strip()

        if len(theme) > 50:
            await message.answer("Слишком длинно. Опишите деятельность автора до 50 символов.")
            return True

        if not theme:
            await message.answer("Напишите хотя бы короткое описание.")
            return True

        data = storage.get(peer_id)
        if not data:
            await bot.state_dispenser.set(peer_id, RecommendState.WAITING_LINK)
            await message.answer("Что-то пошло не так. Пришлите ссылку заново.")
            return True

        sheets.add_author_recommendation(
            url=data["url"],
            normalized=data["normalized"],
            platform=data["platform"],
            theme=theme
        )

        await safe_delete_state(bot, peer_id)
        safe_storage_delete(storage, peer_id)

        await message.answer(
            "Спасибо за Вашу рекомендацию! Будем рады получить несколько рекомендаций.",
            keyboard=main_keyboard
        )
        return True

    return False