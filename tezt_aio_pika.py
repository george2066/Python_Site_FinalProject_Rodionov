import asyncio

import aio_pika


async def on_message(message):
    body = message.body.decode("utf-8")
    print(f"Received message: {body}")
    # Тут можно добавить обработку сообщения


async def main():
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


if __name__ == "__main__":
    asyncio.run(main())
