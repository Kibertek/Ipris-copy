import random

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import VK_TOKEN
from services.price import calculate_print_price
from services.products import get_available_products
from services.branches import load_branches, get_branch_by_id


# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def create_main_keyboard():
    """
    Главное меню бота.
    """

    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        "🖨 Цены на печать",
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_line()

    keyboard.add_button(
        "📦 Что изготавливаем?",
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_line()

    keyboard.add_button(
        "📍 Филиалы",
        color=VkKeyboardColor.PRIMARY
    )

    return keyboard.get_keyboard()


def create_branches_keyboard():
    """
    Клавиатура со списком филиалов.
    """

    keyboard = VkKeyboard(one_time=True)

    branches = load_branches()

    for branch in branches:
        keyboard.add_button(
            branch["name"],
            color=VkKeyboardColor.PRIMARY
        )

        keyboard.add_line()

    keyboard.add_button(
    "⬅ Главное меню",
    color=VkKeyboardColor.SECONDARY
    )

    return keyboard.get_keyboard()


def create_back_keyboard():
    """
    Кнопка возврата в главное меню.
    """

    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        "⬅ Главное меню",
        color=VkKeyboardColor.SECONDARY
    )

    return keyboard.get_keyboard()


# ============================================================
# ОТПРАВКА СООБЩЕНИЙ
# ============================================================

def send_message(vk, user_id, message, keyboard=None):
    """
    Отправляет сообщение пользователю.
    """

    vk.messages.send(
        user_id=user_id,
        random_id=random.randint(1, 2_000_000_000),
        message=message,
        keyboard=keyboard
    )


# ============================================================
# ПРИВЕТСТВИЕ
# ============================================================

def send_welcome(vk, user_id):
    """
    Приветственное сообщение.
    """

    message = (
        "Здравствуйте! 👋\n\n"
        "Я бот копицентра и могу помочь узнать:\n\n"
        "🖨 стоимость печати\n"
        "📦 что мы изготавливаем\n"
        "📍 адреса филиалов\n\n"
        "Выберите нужный раздел ниже."
    )

    send_message(
        vk,
        user_id,
        message,
        create_main_keyboard()
    )


# ============================================================
# ЦЕНЫ
# ============================================================

def send_print_help(vk, user_id):
    """
    Показывает пользователю пример запроса для расчёта.
    """

    message = (
        "🖨 Расчёт стоимости печати\n\n"
        "Напишите количество, формат и тип печати.\n\n"
        "Например:\n\n"
        "50 листов А4 ч/б\n"
        "30 листов А4 цветных\n"
        "20 листов А3 ч/б\n"
        "100 листов А3 цветных"
    )

    send_message(
        vk,
        user_id,
        message,
        create_back_keyboard()
    )


def handle_print_request(vk, user_id, text):
    """
    Обрабатывает запрос стоимости печати.
    """

    words = text.replace(",", " ").split()

    # --------------------------------------------------------
    # Ищем количество
    # --------------------------------------------------------

    quantity = None

    for word in words:
        if word.isdigit():
            quantity = int(word)
            break

    if quantity is None:
        send_message(
            vk,
            user_id,
            "Не удалось определить количество листов.\n\n"
            "Например:\n"
            "50 листов А4 ч/б",
            create_back_keyboard()
        )
        return

    if quantity <= 0:
        send_message(
            vk,
            user_id,
            "Количество листов должно быть больше нуля.",
            create_back_keyboard()
        )
        return

    # --------------------------------------------------------
    # Определяем формат
    # --------------------------------------------------------

    if "а4" in text:
        format_name = "A4"

    elif "а3" in text:
        format_name = "A3"

    else:
        send_message(
            vk,
            user_id,
            "Пока я умею рассчитывать печать только "
            "форматов А4 и А3.",
            create_back_keyboard()
        )
        return

    # --------------------------------------------------------
    # Определяем тип печати
    # --------------------------------------------------------

    if (
        "ч/б" in text
        or "чб" in text
        or "черно-бел" in text
        or "черно бел" in text
        or "чёрно-бел" in text
        or "чёрно бел" in text
    ):
        print_type = "bw"
        type_name = "чёрно-белая"

    elif (
        "цвет" in text
        or "цветн" in text
    ):
        print_type = "color"
        type_name = "цветная"

    else:
        send_message(
            vk,
            user_id,
            "Укажите тип печати: ч/б или цветная.\n\n"
            "Например:\n"
            "50 листов А4 ч/б",
            create_back_keyboard()
        )
        return

    # --------------------------------------------------------
    # Расчёт
    # --------------------------------------------------------

    result = calculate_print_price(
        format_name,
        print_type,
        quantity
    )

    if result is None:
        send_message(
            vk,
            user_id,
            "Для такого варианта печати пока нет цены "
            "в нашем прайсе.",
            create_back_keyboard()
        )
        return

    # --------------------------------------------------------
    # Формируем ответ
    # --------------------------------------------------------

    message = (
        "🖨 Расчёт стоимости\n\n"
        f"Формат: {format_name}\n"
        f"Тип печати: {type_name}\n"
        f"Количество: {quantity} листов\n"
        f"Цена за лист: {result['price_per_sheet']} ₽\n\n"
        f"💰 Итого: {result['total_price']} ₽"
    )

    send_message(
        vk,
        user_id,
        message,
        create_main_keyboard()
    )


# ============================================================
# ПРОДУКЦИЯ
# ============================================================

def send_products(vk, user_id):
    """
    Показывает список продукции.
    """

    products = get_available_products()

    if not products:
        send_message(
            vk,
            user_id,
            "Сейчас список продукции пуст.",
            create_back_keyboard()
        )
        return

    message = "📦 Мы изготавливаем:\n\n"

    for product in products:
        message += f"• {product['name']}\n"

    message += (
        "\nЕсли вас интересует конкретная продукция, "
        "напишите её название."
    )

    send_message(
        vk,
        user_id,
        message,
        create_back_keyboard()
    )


# ============================================================
# ФИЛИАЛЫ
# ============================================================

def send_branches(vk, user_id):
    """
    Показывает список филиалов.
    """

    branches = load_branches()

    if not branches:
        send_message(
            vk,
            user_id,
            "Список филиалов пока пуст.",
            create_back_keyboard()
        )
        return

    send_message(
        vk,
        user_id,
        "📍 Выберите филиал, в котором хотите "
        "получить заказ:",
        create_branches_keyboard()
    )


def handle_branch_selection(vk, user_id, text):
    """
    Проверяет, выбрал ли пользователь существующий филиал.
    """

    branches = load_branches()

    for branch in branches:

        if text.lower() == branch["name"].lower():

            message = (
                f"📍 {branch['name']}\n\n"
                f"Адрес:\n"
                f"{branch['address']}\n\n"
                "Этот филиал выбран для получения заказа."
            )

            send_message(
                vk,
                user_id,
                message,
                create_main_keyboard()
            )

            return True

    return False


# ============================================================
# ОБРАБОТКА СООБЩЕНИЙ
# ============================================================

def handle_message(vk, user_id, text):
    """
    Главная обработка сообщений пользователя.
    """

    text_lower = text.lower().strip()

    # --------------------------------------------------------
    # Приветствие
    # --------------------------------------------------------

    if text_lower in [
        "начать",
        "старт",
        "/start",
        "привет",
        "здравствуйте",
        "добрый день",
        "добрый вечер",
        "доброе утро"
    ]:
        send_welcome(vk, user_id)
        return

    # --------------------------------------------------------
    # Главное меню
    # --------------------------------------------------------

    if text_lower in [
        "главное меню",
        "⬅ главное меню"
    ]:
        send_welcome(vk, user_id)
        return

    # --------------------------------------------------------
    # Цены
    # --------------------------------------------------------

    if text_lower in [
        "цены на печать",
        "🖨 цены на печать"
    ]:
        send_print_help(vk, user_id)
        return

    # --------------------------------------------------------
    # Продукция
    # --------------------------------------------------------

    if text_lower in [
        "что изготавливаем?",
        "📦 что изготавливаем?"
    ]:
        send_products(vk, user_id)
        return

    # --------------------------------------------------------
    # Филиалы
    # --------------------------------------------------------

    if text_lower in [
        "филиалы",
        "📍 филиалы"
    ]:
        send_branches(vk, user_id)
        return

    # --------------------------------------------------------
    # Выбор филиала
    # --------------------------------------------------------

    if handle_branch_selection(vk, user_id, text):
        return

    # --------------------------------------------------------
    # Попытка определить запрос печати
    # --------------------------------------------------------

    if (
        "лист" in text_lower
        or "листа" in text_lower
        or "листов" in text_lower
        or "а4" in text_lower
        or "а3" in text_lower
    ):
        handle_print_request(
            vk,
            user_id,
            text_lower
        )
        return

    # --------------------------------------------------------
    # Если бот не понял запрос
    # --------------------------------------------------------

    send_message(
        vk,
        user_id,
        "Я пока не понял запрос. 🤔\n\n"
        "Выберите нужный раздел:",
        create_main_keyboard()
    )


# ============================================================
# ЗАПУСК БОТА
# ============================================================

def main():
    print("Запуск VK-бота...")

    # Создаём сессию VK
    vk_session = vk_api.VkApi(
        token=VK_TOKEN
    )

    # Получаем API
    vk = vk_session.get_api()

    # Подключаем Long Poll
    longpoll = VkLongPoll(
        vk_session
    )

    print("Бот запущен и ожидает сообщения.")

    # Слушаем новые сообщения
    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:

                user_id = event.user_id
                text = event.text

                print(
                    f"Сообщение от {user_id}: {text}"
                )

                try:

                    handle_message(
                        vk,
                        user_id,
                        text
                    )

                except Exception as error:

                    print(
                        f"Ошибка при обработке сообщения: {error}"
                    )

                    send_message(
                        vk,
                        user_id,
                        "Произошла ошибка при обработке запроса. "
                        "Попробуйте ещё раз."
                    )


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

if __name__ == "__main__":
    main()