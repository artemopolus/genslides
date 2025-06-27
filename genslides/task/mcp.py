
"""
Реализация KeyCraftTask для работы с MCPClient через AsyncRunner.
Использует два последовательных вызова updateIternal:
 1) Подключение и очередь запросов;
 2) Проверка результатов: если не готовы — повторная проверка в следующем вызове;
    иначе — вывод результатов, очистка, и возврат к начальному шагу.
"""
from genslides.task.text import TextTask, TaskDescription
from genslides.helpers.async_runner import AsyncRunner
from genslides.mcp.mcpclient import MCPClient

class MCPTask(TextTask):
    def __init__(self, task_info : TaskDescription):
        super().__init__(task_info, type="MCP")
        self.runner = AsyncRunner()
        self.client = MCPClient()
        self._step = 0
        self._futures = []

    def updateIternal(self, input : TaskDescription =None):
        cres, cparam = self.getParamStruct("mcp_config", only_current=True)
        mres, mparam = self.getParamStruct("model")
        messages = self.getParent().getMsgs()

        if not cres or not mres:
            return None
        
        if cparam.get("block", False):
            results = self._execute_block(messages, cparam, mparam)
            # content = "; ".join(results)
            # self.appendMessage({"role": self.prompt_tag, "content": content})
            return super().updateIternal(input)

        # Асинхронный режим
        if self._step == 0:
            self._execute_async(messages, cparam, mparam)
            return super().updateIternal(input)

        if self._step == 1:
            if not all(fut.done() for _, fut in self._futures):
                pending = [name for name, fut in self._futures if not fut.done()]
                self.updateUpdationInfo( f"Still processing steps: {pending}." )
                return super().updateIternal(input)
            # Финализация
            results = self._finalize_async(cparam)
            content = "\n".join(results) + "\nCleanup done. Ready for new input."
            self.updateUpdationInfo(f"Final:\n{content}")
            # self.appendMessage({"role": self.prompt_tag, "content": content})
            return super().updateIternal(input)

        return None


    def _execute_block(self, messages : list[dict], mcp_params : dict, model_params : dict):
        """
        Блокирующее выполнение: подключение, обработка, очистка.
        """
        results = []
        # Подключение
        try:
            fut = self.runner.submit(
                self.client.connect_to_server(mcp_params.get("path_to_server",""))
            )
            fut.result(timeout= mcp_params.get("connect_timeout",10))
            self.updateUpdationInfo("'connect': OK")
        except Exception as e:
            self.updateUpdationInfo(f"'connect': Error: {e}")
        # Обработка
        try:
            fut = self.runner.submit(
                self.client.process_query(messages, model_params)
            )
            proc_res = fut.result(timeout=mcp_params.get("submit_timeout", 30))
            self.updateUpdationInfo(f"'process': {proc_res}")
        except Exception as e:
            self.updateUpdationInfo(f"'process': Error: {e}")
        # Очистка
        try:
            self.runner.submit(self.client.cleanup()).result(timeout=mcp_params.get("cleanup_timeout", 5))
            self.updateUpdationInfo("'cleanup': OK")
        except Exception as e:
            self.updateUpdationInfo(f"'cleanup': Error: {e}")
        # Остановка
        self.runner.stop()
        return results
    
    def _execute_async(self, messages : list[dict], mcp_params : dict, model_params : dict):
        """
        Неблокирующее выполнение: шаг соединения и обработки, сохранение futures.
        """
        conn_fut = self.runner.submit(
            self.client.connect_to_server(mcp_params.get("path_to_server",""))
        )
        proc_fut = self.runner.submit(
            self.client.process_query(messages, model_params)
        )
        self._futures = [("connect", conn_fut), ("process", proc_fut)]
        self._step = 1
        self.updateUpdationInfo(f"Started connection and message processing (count={len(messages)}).")

    def _finalize_async(self, mcp_params : dict):
        """
        Финализирует асинхронный режим: ожидает futures, собирает результаты, выполняет cleanup и останавливает runner.
        Возвращает список строк с результатами.
        """
        # results = []
        # Ожидание и сбор результата
        for name, fut in self._futures:
            try:
                res = fut.result()
            except Exception as e:
                res = f"Error: {e}"
            self.updateUpdationInfo(f"{name!r}: {res}")
        # Очистка клиента
        try:
            self.runner.submit(self.client.cleanup()).result(timeout=mcp_params.get("cleanup_timeout", 5))
        except Exception:
            pass
        # Остановка runner
        self.runner.stop()
        # Сброс шага
        self._step = 0

