from vkbottle import BaseStateGroup


class RecommendState(BaseStateGroup):
    WAITING_LINK = "waiting_link"
    WAITING_THEME = "waiting_theme"


class FocusState(BaseStateGroup):
    FIO = "fio"
    AGE = "age"
    STATUS = "status"
    ABOUT = "about"