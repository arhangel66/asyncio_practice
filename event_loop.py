import asyncio
import datetime
import logging
import signal
import sys
import time
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

class ConnectedClient:
    def __init__(self, writer: StreamWriter):
        self.writer = writer
        self.get_msg()

    def get_msg(self):
        self.last_message_at = time.time()

    async def write(self, data: str):
        self.writer.write(data)
        await self.writer.drain()

async def handle_client(reader, writer):
    client = ConnectedClient(writer)
    clients.append(client)
    await listen_loop(client, reader, writer)


async def listen_loop(client, reader, writer):
    try:
        while True:
            data = await reader.read(100)
            client.get_msg()
            if not data:
                break
    finally:
        clients.remove(client)
        writer.close()
        await writer.wait_closed()


async def send_status():
    while True:
        await asyncio.sleep(2)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'Current time: {now}, connected clients: {len(clients)}\n'
        for client in clients:
            await client.write(message.encode())
            inactive_time = time.time() - client.last_message_at
            if 10 > inactive_time > 5:
                await client.write(b'You are inactive for 5 seconds, warning\n')
            elif inactive_time > 10:
                await client.write(b'You are inactive for 10 seconds, closing connection\n')
                client.writer.close()
                await client.writer.wait_closed()
                clients.remove(client)
                logger.info(f'Connection closed due to inactivity, {len(clients)} clients left')


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
