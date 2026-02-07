import asyncio
import json
import os

import aio_pika
import django
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.http import Http404
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv

from tg_bot.form import Form

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diplom.settings")

django.setup()

from advertisements.models import Advertisement
from users.models import User

bot = Bot(
    token=os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите ваш username:")
    await state.set_state(Form.waiting_for_login)


@dp.message(F.text, Form.waiting_for_login)
async def save_username(message: Message, state: FSMContext):
    username = message.text
    try:
        user = await sync_to_async(lambda: get_object_or_404(User, username=username))()
        await message.answer("Так, теперь введите ваш пароль:")
        await state.update_data(username=message.text)
        await state.set_state(Form.waiting_for_password)
    except Http404:
        await message.answer(
            "Пользователь не найден. Пожалуйста, начните заново.\nПравда, если вы не зарегистрированы на сайте, то вам срочно нужно зарегистрироваться😄"
        )


@dp.message(F.text, Form.waiting_for_password)
async def save_password(message: Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    username = data.get("username")

    try:
        user = await sync_to_async(lambda: get_object_or_404(User, username=username))()
        if user.check_password(password):
            await sync_to_async(lambda: setattr(user, "chat_id", message.chat.id))()
            await sync_to_async(user.save)()
            await message.answer(
                "Готово! Теперь вам будут приходить сюда уведомления😄"
            )
            await state.clear()
        else:
            await message.answer("Неверный пароль. Попробуйте заново.")
            await state.set_state(Form.waiting_for_password)
    except Http404:
        await message.answer("Пользователь не найден. Пожалуйста, начните заново.")
        await cmd_start(message, state)


async def send_telegram_message(photo_url, caption, chat_id):
    await bot.send_photo(
        chat_id=chat_id, photo=photo_url, caption=caption, parse_mode="HTML"
    )


async def on_message(message):
    # body — байтовая строка
    message_str = message.body.decode("utf-8")  # преобразуем байты в строку
    data = json.loads(message_str)  # парсим JSON

    # Предположим, что нужное поле - 'advertisement'
    advertisement_id = data.get("advertisement", "")
    renter_id = data.get("renter", "")

    renter = await sync_to_async(lambda: User.objects.get(pk=renter_id))()
    advertisement = await sync_to_async(
        lambda: Advertisement.objects.get(pk=advertisement_id)
    )()

    image_url = advertisement.image_url
    title = advertisement.title
    description = advertisement.description
    author = await sync_to_async(lambda: advertisement.author)()
    telegram = renter.telegram
    phone = renter.phone
    email = renter.email
    chat_id = advertisement.author.chat_id
    print(chat_id)

    if not chat_id:
        return

    text = f"""
Telegram: {telegram if telegram else "нет"}
Phone: {phone if phone else "нет"}
Phone: {email if email else "нет"}
Title: {title}
Description: {description}
Рентер: {renter}
Объявление: {advertisement}
Автор объявления: {author}
    """

    await send_telegram_message(image_url, text, chat_id)


async def receiving():
    connection = await aio_pika.connect_robust(
        host="localhost", port=5672, login="guest", password="guest"
    )

    async with connection:
        channel = await connection.channel()
        queue_name = "rent_create"
        queue = await channel.declare_queue(queue_name, durable=True)

        # Получение сообщений через асинхронный итератор
        async for message in queue.iterator():
            async with message.process():
                await on_message(message)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(receiving())
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен разработчиком")
