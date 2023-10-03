import asyncio
import signal

# Функция для обработки сигналов
def signal_handler(task, signal):
    print(f'Received signal {signal}, cancelling the task...')
    task.cancel()

# Асинхронная функция main
async def main():
    print('Event loop running...')
    try:
        while True:
            await asyncio.sleep(1)
            print('Still running...')
    except asyncio.CancelledError:
        print('Task has been cancelled')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main())

    # Добавление обработчиков сигналов
    loop.add_signal_handler(signal.SIGINT, signal_handler, task, 'SIGINT')
    loop.add_signal_handler(signal.SIGTERM, signal_handler, task, 'SIGTERM')

    try:
        loop.run_until_complete(task)
    finally:
        print('Cleaning up and shutting down...')
        loop.close()
