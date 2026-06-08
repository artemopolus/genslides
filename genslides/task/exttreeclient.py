import asyncio
import threading
import concurrent.futures
from typing import Optional

import genslides.task.load as BaseTask
import genslides.utils.loader as Loader
from genslides.task_tools.commander_client import AsyncExternalCommanderPipeline, PipelineInitializationError

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
            try:
                # Пытаемся инициализировать
                init_result = await pipeline.ensure_initialized(
                    session_name=session,
                    actioner_path=actioner
                )
                
                # Если успешно — выполняем экшены
                actions_result = await pipeline.run_actions(actions)
                
                return {
                    "success": True,
                    "initialization": init_result,
                    "execution": actions_result
                }
                
            except PipelineInitializationError as e:
                # Если упало на этапе инициализации — спасаем логи!
                return {
                    "success": False,
                    "error": str(e),
                    "initialization": {
                        "status": "failed",
                        "log": e.log  # Логи до момента падения здесь
                    },
                    "execution": {
                        "status": "not_started",
                        "log": ["Выполнение команд не было запущено из-за ошибки инициализации."]
                    }
                }

    # ===================== MAIN =====================

    def updateIternal(self, input: BaseTask.TextTask.TaskDescription = None):
        if self.isParentFrozen():
            self.updateUpdationInfo("Skipping update: parent is frozen")
            return super().updateIternal(input)
            
        eres, eparam = self.getParamStruct("exttreeclient")
        self.freezeTask()

        if not eres:
            self.updateUpdationInfo("Skipping update: No structure found for 'exttreeclient'")
            return super().updateIternal(input)
            
        check_msgs = eparam.get("check_msgs", True)
        if self._is_completed:
            if check_msgs and self.checkParentMsgList(update=True, save_curr=False):
                self.updateUpdationInfo("Skipping update: Task already marked as completed")
                self.unfreezeTask()
                return super().updateIternal(input)
            else:
                self._is_completed = False

        actions_on = self.findKeyParam(eparam.get("actions_on"))
        if not actions_on:
            self.updateUpdationInfo("Skipping update: 'actions_on' parameter evaluation returned false/empty")
            return super().updateIternal(input)


        # 1. Если задача ещё не запущена → извлекаем параметры и стартуем
        if self._future is None:
            self.updateUpdationInfo("Initializing external pipeline arguments...")
            
            url = self.findKeyParam(eparam.get("url"))
            session = self.findKeyParam(eparam.get("session"))
            actioner = self.findKeyParam(eparam.get("actioner"))
            actions_str = self.findKeyParam(eparam.get("updt_actions", ""))

            jres, actions, jreport = Loader.Loader.loadJsonFromTextStr(actions_str)
            if not jres:
                self.updateUpdationInfo(f"Error on json load {jreport}")
                return super().updateIternal(input)
            if not isinstance( actions, list):
                self.updateUpdationInfo(f"Actions item is not list:\n\n{actions_str}]\n\n===dumps===\n\n{actions}")
                return super().updateIternal(input)

            self.updateUpdationInfo(f"Submitting async pipeline task to background thread (URL: {url}, Session: {session})")
            
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
            self.updateUpdationInfo("Async task is still execution in background thread. Polling...")
            return super().updateIternal(input)

        # 3. Если завершилась → забираем результат
        try:
            self._result = self._future.result()
            self.updateUpdationInfo("Async pipeline execution completed successfully. Unfreezing.")
            self.unfreezeTask()
        except Exception as e:
            self._result = {"status": "error", "error": str(e)}
            self.updateUpdationInfo(f"Async pipeline execution failed with exception: {str(e)}")

        self._apply_result(eparam, self._result)
        self._future = None
        self._is_completed = True 

        return super().updateIternal(input)

    # ===================== HELPERS =====================

    def _apply_result(self, param: dict, result: dict):
        param["result"] = result
        self.setParamStruct(param)
        if "execution" in result:
            if "report" in result["execution"]:
                try:
                    reports = result["execution"]["report"]
                    text = reports[-1]["report"]["prompt"]
                    self.appendPrompt( text )
                except Exception as e:
                    self.updateUpdationInfo(f"Ext Client error:{e}")
            else:
                self.updateUpdationInfo(f"Ext Client error: no report")
        else:
            self.updateUpdationInfo(f"Ext Client error: no report")

                    
        