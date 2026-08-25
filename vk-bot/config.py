import os

from dotenv import load_dotenv


load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")

if not VK_TOKEN:
    raise ValueError(
        "Не найден VK_TOKEN. "
        "Создай файл .env и добавь туда токен сообщества."
    )