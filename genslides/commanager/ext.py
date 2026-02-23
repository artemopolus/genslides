# genslides/commanager/ext.py
from typing import Any, Dict, List
import threading
import json
import hashlib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import genslides.commanager.com as Commander  # ваш базовый класс

class _ReqModel(BaseModel):
    data: Dict[str, Any]
    hash: str

class _RespModel(BaseModel):
    status: str
    sessions: List[str]
    hash: str

class _StdGenslidesRespModel(BaseModel):
    status: str
    data: Dict[str,Any]
    hash: str


class _CustomRespModel(BaseModel):
    status: str
    type: str = "custom_command"
    result: Any          # Результаты выполнения списка команд
    actioners: List[str]        # Список всех имен Актионеров
    current_actioner: str       # Имя текущего Актионера
    tasks: List[Dict[str, Any]] # Список словарей задач
    hash: str

def _compute_hash(data: Dict[str, Any]) -> str:
    """
    Считаем SHA-256 от канонического JSON: сортированные ключи, компактные separators.
    """
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ExternalCommander(Commander.Commander):
    def __init__(self, path: str = "session"):
        super().__init__(path)
        # FastAPI app
        self.app = FastAPI(title="ExternalCommander API")
        self._register_routes()

    def getSessionNameList(self) -> List[str]:
        """
        Используйте реализацию в базовом классе Commander.Commander (вызов super).
        Оставляем метод для удобства и возможной переопределённости.
        """
        return super().getSessionNameList()

    def _register_routes(self) -> None:
        @self.app.post("/sessions", response_model=_RespModel)
        def sessions_endpoint(req: _ReqModel):
            """
            Ожидает JSON:
            {
              "data": { ... },   # произвольный объект (может быть {} если не нужен)
              "hash": "..."      # hex SHA-256 от canonical json(data)
            }

            Возвращает:
            {
              "status": "ok",
              "sessions": [...],
              "hash": "..."   # пересчитанный hash от returned data (для проверки на клиенте)
            }
            """
            # Проверка целостности входа
            calc = _compute_hash(req.data)
            if calc != req.hash:
                raise HTTPException(status_code=400, detail="Hash mismatch")

            # Получаем список сессий
            try:
                sessions = list(self.getSessionNameList())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get sessions: {e}")

            # Для ответа формируем data_out и hash_out
            data_out = {"sessions": sessions}
            hash_out = _compute_hash(data_out)

            return {"status": "ok", "sessions": sessions, "hash": hash_out}

        @self.app.post("/gs_cmd", response_model=_StdGenslidesRespModel)
        def genslides_command_endpoint(req: _ReqModel):
            print(f"Genslides command:{req.data}")
           # Проверка целостности входа
            calc = _compute_hash(req.data)
            if calc != req.hash:
                raise HTTPException(status_code=400, detail="Hash mismatch")
            
            payload = getattr(req.data,"payload_data",{})

            cmd_type = getattr(payload,"cmd_type","")
            data_out = {"test": []}
            if cmd_type == "load_session":
                pass
            elif cmd_type == "set_actioners":
                pass
            elif cmd_type == "get_actioners":
                pass
            elif cmd_type == "get_tasks":
                pass
            elif cmd_type == "get_task_info":
                pass

            # Для ответа формируем data_out и hash_out
            hash_out = _compute_hash(data_out)

            return {"status": "ok", "data": data_out, "hash": hash_out}


        
        @self.app.post("/custom_command", response_model=_CustomRespModel)
        def custom_command_endpoint(req: _ReqModel):
            print('custom_command')
            # 1. Проверка хэша всей структуры data
            # (той самой internal_data из Godot)
            calc = _compute_hash(req.data)
            if calc != req.hash:
                raise HTTPException(status_code=400, detail="Hash mismatch")

            # 2. Извлекаем список команд из payload_data
            # В Godot ты передал это как второй аргумент в send_command
            actions = req.data.get("payload_data", [])
            
            if not isinstance(actions, list):
                raise HTTPException(status_code=400, detail="payload_data must be a list for custom_command")

            results = "All done"
            
            # 3. Выполняем каждую команду из списка
            # try:
            #     for item in actions:
            #         action_name = item.get("action")
            #         kwargs = item.get("kwargs", {})
                    
            #         # Вызываем метод выполнения в твоем базовом классе Commander
            #         # Допустим, он называется execute_action
            #         res = self.execute_action(action_name, **kwargs)
            #         results.append(res)
            # except Exception as e:
            #     raise HTTPException(status_code=500, detail=f"Execution error: {e}")
            response_data = {
                "status": "ok",
                "type": "custom_command",
                "result": results,
                "actioners": [],
                "current_actioner": "None",
                "tasks": []
            }

            # 4. Собираем данные для ответа, как ты просил
            # try:
            #     all_actioners = list(self.getSessionNameList()) # или getActionerList()
            #     # Получаем текущего актионера (замени на свой метод)
            #     current_act = self.current_session 
            #     # Получаем список задач (замени на свой метод)
            #     current_tasks = self.get_tasks_for_actioner(current_act) 
            # except Exception as e:
            #     raise HTTPException(status_code=500, detail=f"State gathering error: {e}")

            # # 5. Формируем финальный словарь ответа
            # response_data = {
            #     "status": "ok",
            #     "type": "custom_command",
            #     "result": results,
            #     "actioners": all_actioners,
            #     "current_actioner": str(current_act),
            #     "tasks": current_tasks
            # }

            # 6. Считаем хэш ответа для проверки в Godot
            response_data["hash"] = _compute_hash(response_data)
            
            return response_data

    def start_server(self, host: str = "0.0.0.0", port: int = 8000, daemon: bool = True) -> threading.Thread:
        """
        Запускает uvicorn в фоновом потоке. Возвращает поток.
        Для быстрого прототипа — запускаем через uvicorn.run(self.app, ...)
        """
        import uvicorn

        def _run():
            # Прямой запуск данного FastAPI приложения
            uvicorn.run(self.app, host=host, port=port, log_level="info")

        thread = threading.Thread(target=_run, daemon=daemon, name="ExternalCommander-uvicorn")
        thread.start()
        return thread
