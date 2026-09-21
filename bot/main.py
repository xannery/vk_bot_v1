from vkbottle.bot import Bot, Message
from vkbottle import CtxStorage

from bot.config import TOKEN, ADMINS
from bot.keyboards import main_keyboard
from bot.handlers import menu, recommend, focus


bot = Bot(token=TOKEN)
storage = CtxStorage()


@bot.on.private_message()
async def handler(message: Message):
    peer_id = message.peer_id
    current_state = await bot.state_dispenser.get(peer_id)
    state_name = str(current_state).lower() if current_state else ""

    # Сначала пробуем обработать активные сценарии
    if state_name:
        if await recommend.handle_recommend(message, bot, storage, state_name):
            return
        if await focus.handle_focus(message, bot, storage, state_name):
            return

    # Если сценариев нет — обрабатываем меню
    handled = await menu.handle_menu(message, bot, storage)
    if handled:
        return

    # Fallback — показываем меню
    await message.answer(
        "Коллектив ЯЛОН на связи!\nВыберите в меню, что хотите сделать:",
        keyboard=main_keyboard
    )


if __name__ == "__main__":
    print("Бот успешно запущен")
    bot.run_forever()