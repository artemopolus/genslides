import asyncio
import threading
import concurrent.futures
from typing import Optional

import genslides.task.load as BaseTask
import genslides.utils.loader as Loader
from genslides.task_tools.commander_client import AsyncExternalCommanderPipeline

# ===================== GLOBAL ASYNC SETUP =====================
_bg_loop = asyncio.new_event_loop()

def _start_background_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

_bg_thread = threading.Thread(
    target=_start_background_loop, 
    args=(_bg_loop,), 
    daemon=True,
    name="AsyncWorkerThread"
)
_bg_thread.start()


class ExtTreeClientTask(BaseTask.LoadTask):
    def __init__(self, task_info: BaseTask.TextTask.TaskDescription):
        super().__init__(task_info, type="ExtTreeClient")

        # runtime state
        self._future: Optional[concurrent.futures.Future] = None
        self._result = None
        self._is_completed: bool = False

    # ===================== ASYNC JOB =====================

    async def _run_pipeline(self, url: str, session: str, actioner: Optional[str], actions: list):
        """
        Чистая корутина: больше ничего не знает про структуру eparam.
        Принимает только строго определенные аргументы.
        """
        async with AsyncExternalCommanderPipeline(base_url=url) as pipeline:
            await pipeline.ensure_initialized(
                session_name=session,
                actioner_path=actioner
            )
            return await pipeline.run_actions(actions)

    # ===================== MAIN =====================

    def updateIternal(self, input: BaseTask.TextTask.TaskDescription = None):
        eres, eparam = self.getParamStruct("exttreeclient")
        self.freezeTask()

        if not eres or self._is_completed:
            return super().updateIternal(input)
        actions_on = self.findKeyParam( eparam.get("actions_on") )

        if not actions_on:
            return super().updateIternal(input)

        check_msgs = self.findKeyParam( eparam.get("check_msgs") )

        if self._future is None and check_msgs and self.checkParentMsgList(update=True, save_curr=False):
            self.updateUpdationInfo(f"Hash is same")
            self.unfreezeTask()
            return super().updateIternal(input)
        # 1. Если задача ещё не запущена → извлекаем параметры и стартуем
        if self._future is None:
            # Вся работа с eparam локализована здесь
            url = self.findKeyParam( eparam.get("url") )
            session = self.findKeyParam( eparam.get("session") )
            actioner =self.findKeyParam(  eparam.get("actioner") )
            actions_str = self.findKeyParam( eparam.get("updt_actions", []) )

            jres, actions, jreport = Loader.Loader.loadJsonFromTextStr( actions_str )
            if not jres:
                self.updateUpdationInfo(f"Error on json load {jreport}")
                return super().updateIternal(input)


            # Передаем в фоновый поток уже готовые, чистые типы данных
            self._future = asyncio.run_coroutine_threadsafe(
                self._run_pipeline(
                    url=url,
                    session=session,
                    actioner=actioner,
                    actions=actions
                ), 
                _bg_loop
            )
            return super().updateIternal(input)

        # 2. Если выполняется → просто выходим (non-blocking)
        if not self._future.done():
            return super().updateIternal(input)

        # 3. Если завершилась → забираем результат
        try:
            self._result = self._future.result()
            self.unfreezeTask()
        except Exception as e:
            self._result = {"status": "error", "error": str(e)}

        self._apply_result(eparam, self._result)
        self._future = None
        self._is_completed = True 

        return super().updateIternal(input)

    # ===================== HELPERS =====================

    def _apply_result(self, param : dict,  result: dict):
        param["result"] = result
        self.setParamStruct( param )

