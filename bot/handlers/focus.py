from vkbottle.bot import Message

from bot.keyboards import main_keyboard
from bot.states import FocusState
from bot.services import sheets
from bot.handlers.menu import safe_delete_state, safe_storage_delete


async def handle_focus(message: Message, bot, storage, state_name: str) -> bool:
    peer_id = message.peer_id
    text = (message.text or "").strip()

    if "fio" in state_name:
        storage.set(peer_id, {"fio": text})
        await bot.state_dispenser.set(peer_id, FocusState.AGE)
        await message.answer("Сколько тебе лет?")
        return True

    if "age" in state_name:
        data = storage.get(peer_id) or {}
        data["age"] = text
        storage.set(peer_id, data)
        await bot.state_dispenser.set(peer_id, FocusState.STATUS)
        await message.answer("Твой статус? (студент / работаю / фриланс / другое)")
        return True

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
        return True

    if "about" in state_name:
        if len(text) > 350:
            await message.answer("Слишком длинно. Пожалуйста, сократите текст до 350 символов.")
            return True

        data = storage.get(peer_id) or {}
        data["about"] = text

        sheets.add_focus_response(
            user_id=message.from_id,
            fio=data.get("fio", ""),
            age=data.get("age", ""),
            status=data.get("status", ""),
            about=data.get("about", "")
        )

        await safe_delete_state(bot, peer_id)
        safe_storage_delete(storage, peer_id)

        await message.answer("Спасибо! Анкета сохранена.", keyboard=main_keyboard)
        return True

    return False