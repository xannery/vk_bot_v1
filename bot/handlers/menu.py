from vkbottle.bot import Message

from bot.config import ADMINS
from bot.keyboards import main_keyboard
from bot.states import RecommendState, FocusState
from bot.services import sheets


async def safe_delete_state(bot, peer_id: int):
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        pass


def safe_storage_delete(storage, peer_id: int):
    try:
        storage.delete(peer_id)
    except KeyError:
        pass


async def handle_menu(message: Message, bot, storage):
    peer_id = message.peer_id
    text_lower = (message.text or "").strip().lower()

    # Админ-команды
    if text_lower == "/stats" and message.from_id in ADMINS:
        authors_count, focus_count = sheets.get_stats()
        await message.answer(
            f"Статистика:\nВсего записей авторов: {authors_count}\nАнкет фокус-группы: {focus_count}"
        )
        return True

    if text_lower == "/export" and message.from_id in ADMINS:
        await message.answer(f"Ссылка на таблицу:\n{sheets.get_spreadsheet_url()}")
        return True

    if text_lower in ["/start", "начать", "старт", "меню"]:
        await safe_delete_state(bot, peer_id)
        safe_storage_delete(storage, peer_id)
        await message.answer(
            "Коллектив ЯЛОН на связи!\nВыберите в меню, что хотите сделать:",
            keyboard=main_keyboard
        )
        return True

    if text_lower == "рекомендация":
        await bot.state_dispenser.set(peer_id, RecommendState.WAITING_LINK)
        await message.answer(
            "Для того, чтобы поделиться рекомендацией на локального автора, Вам необходимо отправить ссылку на личную страницу автора/сообщества/объединения в одной из социальных сетей (VK, Telegram, Instagram, Tik-Tok, Twitch).\n\n"
            "Важно! Рекомендуемый автор должен быть из Удмуртской Республики, его деятельность может осуществляться и за её пределами."
        )
        return True

    if text_lower in ["фг", "фокус", "анкета"]:
        await bot.state_dispenser.set(peer_id, FocusState.FIO)
        await message.answer("Отлично! Давай заполним анкету.\n\nКак тебя зовут? (ФИО)")
        return True

    if text_lower == "другое":
        await safe_delete_state(bot, peer_id)
        safe_storage_delete(storage, peer_id)
        await message.answer(
            "Напишите ваш вопрос — мы ответим в ближайшее время.",
            keyboard=main_keyboard
        )
        return True

    return False