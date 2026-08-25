import random

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import VK_TOKEN
from services.price import calculate_print_price
from services.products import get_available_products
from services.branches import load_branches


def create_main_keyboard():
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        "Цены на печать",
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_line()

    keyboard.add_button(
        "Что изготавливаем?",
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_button(
        "Филиалы",
        color=VkKeyboardColor.PRIMARY
    )

    return keyboard.get_keyboard()


def create_branches_keyboard():
    keyboard = VkKeyboard(one_time=True)

    branches = load_branches()

    for branch in branches:
        keyboard.add_button(
            branch["name"],
            color=VkKeyboardColor.PRIMARY
        )

        keyboard.add_line()

    return keyboard.get_keyboard()


def send_message(vk, user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        random_id=random.randint(1, 2_000_000_000),
        message=message,
        keyboard=keyboard
    )


def handle_message(vk, user_id, text):
    text_lower = text.lower().strip()

    if text_lower in ["начать", "старт", "/start", "привет"]:
        send_message(
            vk,
            user_id,
            "Здравствуйте! Я бот копицентра.\n\n"
            "Могу подсказать стоимость печати, "
            "рассказать о наших услугах и показать филиалы.",
            create_main_keyboard()
        )
        return

    if text_lower == "цены на печать":
        send_message(
            vk,
            user_id,
            "Для расчёта стоимости напишите, например:\n\n"
            "50 листов А4 ч/б\n"
            "30 листов А4 цветных\n"
            "20 листов А3 ч/б"
        )
        return

    if text_lower == "что изготавливаем?":
        products = get_available_products()

        message = "Мы изготавливаем:\n\n"

        for product in products:
            message += f"• {product['name']}\n"

        message += (
            "\nДля уточнения стоимости и оформления заказа "
            "потребуется дополнительная информация."
        )

        send_message(
            vk,
            user_id,
            message,
            create_main_keyboard()
        )
        return

    if text_lower == "филиалы":
        send_message(
            vk,
            user_id,
            "Выберите филиал:",
            create_branches_keyboard()
        )
        return

    # Простая обработка примеров:
    if "лист" in text_lower:
        handle_print_request(vk, user_id, text_lower)
        return

    send_message(
        vk,
        user_id,
        "Я пока не совсем понял запрос.\n\n"
        "Выберите нужный раздел:",
        create_main_keyboard()
    )


def handle_print_request(vk, user_id, text):
    words = text.replace(",", " ").split()

    quantity = None

    for word in words:
        if word.isdigit():
            quantity = int(word)
            break

    if quantity is None:
        send_message(
            vk,
            user_id,
            "Укажите количество листов.\n\n"
            "Например: 50 листов А4 ч/б"
        )
        return

    if "а4" in text:
        format_name = "A4"
    elif "а3" in text:
        format_name = "A3"
    else:
        send_message(
            vk,
            user_id,
            "Пока я умею рассчитывать только А4 и А3."
        )
        return

    if "ч/б" in text or "чб" in text or "черно-бел" in text:
        print_type = "bw"
        type_name = "чёрно-белая"
    elif "цвет" in text:
        print_type = "color"
        type_name = "цветная"
    else:
        send_message(
            vk,
            user_id,
            "Укажите тип печати: ч/б или цветная.\n\n"
            "Например:\n"
            "50 листов А4 ч/б"
        )
        return

    result = calculate_print_price(
        format_name,
        print_type,
        quantity
    )

    if result is None:
        send_message(
            vk,
            user_id,
            "Не удалось найти цену для такого варианта печати."
        )
        return

    message = (
        f"Расчёт стоимости:\n\n"
        f"Формат: {format_name}\n"
        f"Печать: {type_name}\n"
        f"Количество: {quantity} листов\n"
        f"Цена за лист: {result['price_per_sheet']} ₽\n\n"
        f"Итого: {result['total_price']} ₽"
    )

    send_message(
        vk,
        user_id,
        message,
        create_main_keyboard()
    )


def main():
    print("Запуск VK-бота...")

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    print("Бот запущен и ожидает сообщения.")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = event.user_id
                text = event.text

                print(
                    f"Сообщение от {user_id}: {text}"
                )

                handle_message(
                    vk,
                    user_id,
                    text
                )


if __name__ == "__main__":
    main()