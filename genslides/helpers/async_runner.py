# async_runner.py
"""
Утилита для неблокирующего запуска asyncio-корутин в фоновом потоке.
"""
import asyncio
import threading

class AsyncRunner:
    """Запускает собственный asyncio-loop в отдельном потоке для неблокирующих вызовов."""
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        """
        Планирует исполнение корутины `coro` в фоне.
        Возвращает concurrent.futures.Future.
        """
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        """Останавливает event loop и ждёт завершения потока."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

