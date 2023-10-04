import asyncio
import datetime
import logging
import signal
import sys
from asyncio import StreamReader, StreamWriter
from time import sleep

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

def display_datetime():
    print(f'Current datetime: {datetime.datetime.now()}')

async def signal_handler():
    print('Received signal, cancelling tasks...')
    for task in asyncio.all_tasks():
        task.cancel()

clients = []

async def handle_client(reader, writer):
    clients.append(writer)
    try:
        while True:
            data = await reader.read(100)
            if not data:
                break
    finally:
        clients.remove(writer)
        writer.close()
        await writer.wait_closed()

async def send_status():
    while True:
        await asyncio.sleep(2)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'Current time: {now}, connected clients: {len(clients)}\n'
        for client in clients:
            client.write(message.encode())
            await client.drain()

async def create_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8088)
    async with server:
        send_status_task = asyncio.create_task(send_status())
        try:
            await asyncio.Event().wait()  # Keep the server running
        finally:
            send_status_task.cancel()

async def main():
    print('Event loop running...')
    loop.call_later(3, display_datetime)

    try:
        await create_server()
    except asyncio.CancelledError:
        print("Main task was cancelled")



if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    # Добавление обработчиков сигналов
    loop.add_signal_handler(signal.SIGINT, lambda: loop.create_task(signal_handler()))
    loop.add_signal_handler(signal.SIGTERM, lambda: loop.create_task(signal_handler()))

    try:
        loop.run_until_complete(main())
    finally:
        print('Cleaning up and shutting down...')
        loop.close()
