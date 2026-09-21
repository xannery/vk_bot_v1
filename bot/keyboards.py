from vkbottle import Keyboard, Text, KeyboardButtonColor


main_keyboard = (
    Keyboard(one_time=False)
    .add(Text("Рекомендация"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("ФГ"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Другое"), color=KeyboardButtonColor.SECONDARY)
    .get_json()
)