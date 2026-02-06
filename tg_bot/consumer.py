import json
import os

import django
from pika import BlockingConnection
from pika import ConnectionParameters

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diplom.settings")

django.setup()

from advertisements.models import Advertisement
from users.models import User

connection_params = ConnectionParameters(
    host="localhost",
    port=5672,
)


def print_method(ch, method, properties, body):
    # body — байтовая строка
    message_str = body.decode("utf-8")  # преобразуем байты в строку
    data = json.loads(message_str)  # парсим JSON
    print(data)

    # Предположим, что нужное поле - 'advertisement'
    advertisement_id = data.get("advertisement", "")
    renter_id = data.get("renter", "")

    renter = User.objects.get(pk=renter_id)
    advertisement = Advertisement.objects.get(pk=advertisement_id)

    print(renter)
    print(advertisement)

    # подтверждение обработки
    ch.basic_ack(delivery_tag=method.delivery_tag)


def receiving(queue):
    with BlockingConnection(connection_params) as connection:
        with connection.channel() as channel:
            channel.queue_declare(queue, durable=True)

            channel.basic_consume(
                queue=queue,
                on_message_callback=print_method,
            )
            print("Wait messages")
            channel.start_consuming()


if __name__ == "__main__":
    receiving("rent_create")
