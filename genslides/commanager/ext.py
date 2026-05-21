# genslides/commanager/ext.py
from typing import Any, Dict, List, Optional
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
    result: Any                         # Результаты выполнения списка команд
    actioners: List[str]                # Список всех имен Актионеров
    current_actioner: Optional[str]     # Имя текущего Актионера (может быть None)
    report: Any                         # Меняем на Any или str, если getTaskReport() возвращает строку/текст
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
            
            # payload : dict = getattr(req.data,"payload_data",{})
            payload : dict = req.data.get("payload_data",{})

            cmd_type = payload.get("cmd_type","")
            cmd_value = payload.get("cmd_value","")
            data_out = {"report": "empty"}
            result = True
            print(f"Command type: {cmd_type}")
            print(f"VALUE:\n {cmd_value}")
            if cmd_type == "load_session":
                result, report = self.getSessionNameFromList( cmd_value )
                data_out["report"] = report
            elif cmd_type == "set_actioner":
                result = self.setActionerByAnyPath( cmd_value )
                if result:
                    data_out["report"] = self.actioner.getTaskReport()
            elif cmd_type == "load_exttree_actioner":
                data_out ["report"] = self.loadActionersForExtTreeTasks() 

            elif cmd_type == "get_actioners":
                value, choices = self.getActionerPathsList()
                data_out["value"] = value
                data_out["choices"] = choices

            
            elif cmd_type == "set_task":
                result = False
                if isinstance( cmd_value, dict):
                    act_name = cmd_value.get("actioner")
                    task_name = cmd_value.get("task")
                    result = self.setActionerByAnyPath( act_name )
                    if result:
                        task = self.actioner.getCurrentManager().getTaskByAnyName( task_name )
                        if task != None:
                            self.actioner.getCurrentManager().setCurrentTask( task )
                            data_out["report"] = self.actioner.getTaskReport()
                            result = True
                        else:
                            data_out = {"report": "No valid task"}
                    else:
                        data_out = {"report": "No valid actioner"}

                else:
                    data_out = {"report": "cmd value is not dict"}

            # Для ответа формируем data_out и hash_out
            hash_out = _compute_hash(data_out)

            return {"status": "ok" if result else "error", "data": data_out, "hash": hash_out}


        
        @self.app.post("/custom_command", response_model=_CustomRespModel)
        def custom_command_endpoint(req: _ReqModel):
            print('custom_command')
            calc = _compute_hash(req.data)
            if calc != req.hash:
                raise HTTPException(status_code=400, detail="Hash mismatch")

            actions = req.data.get("payload_data", [])
            
            if not isinstance(actions, list):
                raise HTTPException(status_code=400, detail="payload_data must be a list for custom_command")

            results = self.actioner.getJsonCustomCmd(actions)
            
            value, choices = self.getActionerPathsList()

            response_data = {
                "status": "ok",
                "type": "custom_command",
                "result": results,
                "actioners": [ch[0] for ch in choices],
                "current_actioner": value[0],
                "report" : self.actioner.getTaskReport()
            }
            hash_out = _compute_hash(response_data)
            response_data["hash"] = hash_out
            
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
