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
