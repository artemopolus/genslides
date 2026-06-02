import hashlib
import json
import httpx
from typing import Any, Dict, List, Optional

import requests


class ExternalCommanderClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the ExternalCommander API client.

        :param base_url: The base URL of the running FastAPI server.
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Computes SHA-256 hash from canonical JSON (sorted keys, compact separators).
        Matches the server's backend implementation precisely.
        """
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _send_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal helper to wrap payloads, append integrity hashes, 
        and handle response hash validation.
        """
        # 1. Prepare request payload with calculated hash
        payload = {
            "data": data,
            "hash": self._compute_hash(data)
        }
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=payload)
        
        # Raise an exception if HTTP status code is 4xx or 5xx
        response.raise_for_status()
        resp_json = response.json()
        
        # 2. Server-side response hash verification logic
        # Note: server endpoints calculate hash against either data packages or the outer response payload.
        # We handle both patterns based on the specific endpoint design in ext.py
        if endpoint == "/sessions":
            data_to_verify = {"sessions": resp_json.get("sessions")}
            expected_hash = resp_json.get("hash")
        elif endpoint == "/gs_cmd":
            data_to_verify = resp_json.get("data", {})
            expected_hash = resp_json.get("hash")
        elif endpoint == "/custom_command":
            # For custom command, the hash is computed over all keys except the 'hash' key itself
            data_to_verify = {k: v for k, v in resp_json.items() if k != "hash"}
            expected_hash = resp_json.get("hash")
        else:
            data_to_verify = {}
            expected_hash = ""

        # Validate server integrity
        if expected_hash and self._compute_hash(data_to_verify) != expected_hash:
            raise ValueError("Client-side error: Server response hash mismatch. Data might be corrupted.")
            
        return resp_json

    def get_sessions(self) -> List[str]:
        """
        Fetch the list of all active or saved sessions.
        Maps to POST /sessions
        """
        # Expects an empty or generic dict wrapper
        response = self._send_request("/sessions", data={})
        return response.get("sessions", [])

    def send_genslides_command(self, cmd_type: str, cmd_value: Any) -> Dict[str, Any]:
        """
        Sends a core engine management command.
        Maps to POST /gs_cmd
        
        :param cmd_type: 'load_session', 'set_actioner', 'get_actioners', or 'set_task'
        :param cmd_value: String values or configuration Dicts depending on the cmd_type.
        """
        # Server looks for 'payload_data' inside req.data
        data_payload = {
            "payload_data": {
                "cmd_type": cmd_type,
                "cmd_value": cmd_value
            }
        }
        return self._send_request("/gs_cmd", data=data_payload)

    def send_custom_command(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a pipeline batch list of custom operations.
        Maps to POST /custom_command
        
        :param actions: List of dictionaries representing actions to process.
        """
        if not isinstance(actions, list):
            raise TypeError("Actions must be configured inside a list framework.")
            
        data_payload = {
            "payload_data": actions
        }
        return self._send_request("/custom_command", data=data_payload)
    



class AsyncExternalCommanderPipeline:
    def __init__(
        self,
        base_url: str,
        timeout: float = 600.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ===================== LIFECYCLE =====================

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    async def _ensure_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )

    # ===================== CORE =====================

    async def ensure_initialized(
        self,
        session_name: str,
        actioner_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ensures the session and correct actioner are initialized on the server
        following the step-by-step validation and fallback blueprint.
        """
        print(f"\n--- Проверка инициализации для сессии: '{session_name}' ---")
        
        # Проверяем, инициализирована ли уже какая-то сессия на сервере
        choices = await self.get_actioners()
        
        if len(choices) > 0:
            print("Сессия уже инициализирована на сервере. Запуск интерактивного режима напрямую.")
            selected = self._resolve_actioner(choices, actioner_path)
            print(f"Выбран активный актионер: '{selected}'")
            return {
                "status": "already_initialized",
                "actioner": selected
            }
            
        print("Начало процесса первичной загрузки...")
        
        # 1. Запрос списка всех сессий
        sessions = await self.get_sessions()
        if not sessions:
            print("Список сессий на сервере пуст или сервер недоступен. Завершение работы.")
            raise RuntimeError("Session list on the server is empty or the server is unavailable.")
        
        print(f"Успешно получен список доступных сессий с сервера. Всего сессий: {len(sessions)}")

        # Проверяем наличие запрашиваемой сессии на сервере
        if session_name not in sessions:
            print(f"Предупреждение: Сессия '{session_name}' не найдена в списке доступных сессий сервера.")
            print(f"Доступные варианты: {sessions}")

        # 2. Загрузка целевой сессии
        print(f"Отправка запроса на загрузку сессии '{session_name}'...")
        ok = await self.load_session(session_name)
        if not ok:
            print("Ошибка при загрузке сессии. Завершение работы.")
            raise RuntimeError(f"Error loading target session '{session_name}'.")
        
        print(f"Успешно: Сессия '{session_name}' загружена.")

        # 3. Повторный запрос актионеров после загрузки сессии
        print("Запрос доступных актионеров для загруженной сессии...")
        choices = await self.get_actioners()
        if not choices:
            print("Ошибка: Список актионеров пуст после загрузки сессии. Завершение работы.")
            raise RuntimeError("No actioners returned from the engine after session load.")
        
        print(f"Получен список актионеров. Доступно вариантов: {len(choices)}")

        # Разрешение пути актионера и логика fallback
        target_actioner_path = actioner_path if actioner_path else ""
        found = False
        selected = choices[0][1] # По умолчанию берем первый

        for c in choices:
            if c[1].endswith(target_actioner_path):
                selected = c[1]
                found = True
                break

        if not found and target_actioner_path:
            print(f"\nПредупреждение: Указанный актионер '{target_actioner_path}' отсутствует.")
            print(f"Автоматически выбран первый доступный: '{selected}'")
        else:
            print(f"Целевой актионер успешно определен: '{selected}'")

        # 4. Активация выбранного актионера
        print(f"Активация выбранного актионера на сервере...")
        if not await self.set_actioner(selected):
            print("Ошибка при установке активного актионера. Завершение работы.")
            raise RuntimeError(f"Error setting active engine actioner destination to: '{selected}'")
        
        print(f"Успешно: Актионер '{selected}' установлен как активный.")
        print("--- Первичная загрузка и инициализация успешно завершены ---\n")

        return {
            "status": "initialized",
            "actioner": selected
        }


    async def run_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        if not isinstance(actions, list):
            raise TypeError("actions must be a list")

        res = await self._post("/custom_command", {"actions": actions})

        return {
            "status": res.get("status"),
            "result": res.get("result"),
            "actioner": res.get("current_actioner"),
            "actioners": res.get("actioners"),
            "report": res.get("report")
        }

# ===================== API =====================

    async def get_sessions(self) -> List[str]:
        # Server expects an empty or generic dict wrapper for validation
        res = await self._post("/sessions", data={})
        return res.get("sessions", [])

    async def load_session(self, session_name: str) -> bool:
        data_payload = {
            "payload_data": {
                "cmd_type": "load_session",
                "cmd_value": session_name
            }
        }
        res = await self._post("/gs_cmd", data=data_payload)
        return res.get("status") == "ok"

    async def get_actioners(self) -> List[List[str]]:
        data_payload = {
            "payload_data": {
                "cmd_type": "get_actioners",
                "cmd_value": ""
            }
        }
        res = await self._post("/gs_cmd", data=data_payload)
        return res.get("data", {}).get("choices", [])

    async def set_actioner(self, actioner_path: str) -> bool:
        data_payload = {
            "payload_data": {
                "cmd_type": "set_actioner",
                "cmd_value": actioner_path
            }
        }
        # Fixed incorrect endpoint path from "/command" to "/gs_cmd"
        res = await self._post("/gs_cmd", data=data_payload)
        return res.get("status") == "ok"

    async def load_exttree_actioner(self) -> bool:
        data_payload = {
            "payload_data": {
                "cmd_type": "load_exttree_actioner",
                "cmd_value": ""
            }
        }
        # Fixed incorrect endpoint path from "/command" to "/gs_cmd"
        res = await self._post("/gs_cmd", data=data_payload)
        return res.get("status") == "ok"

    async def set_task(self, actioner: str, task: str) -> bool:
        data_payload = {
            "payload_data": {
                "cmd_type": "set_task",
                "cmd_value": {
                    "actioner": actioner,
                    "task": task
                }
            }
        }
        # Fixed incorrect endpoint path from "/command" to "/gs_cmd"
        res = await self._post("/gs_cmd", data=data_payload)
        return res.get("status") == "ok"

    async def run_actions(
        self,
        actions_pipeline: List[Dict[str, List[Dict[str, Any]]]]
    ) -> Dict[str, Any]:
        """
        Runs a sequential pipeline of actions grouped by actioner.
        
        Input format:
        [
            {"actioner_name_1": [action1, action2]},
            {"actioner_name_2": [action3]}
        ]
        """
        if not isinstance(actions_pipeline, list):
            raise TypeError("actions_pipeline must be a list")

        print(f"\n--- Запуск пакетного конвейера действий (Всего групп: {len(actions_pipeline)}) ---")
        
        combined_reports = []
        last_res = {}

        for index, group in enumerate(actions_pipeline, start=1):
            if not isinstance(group, dict) or not group:
                print(f"Предупреждение: Элемент конвейера под индексом {index} имеет неверный формат. Пропуск.")
                continue

            # Извлекаем имя актионера и его список действий
            actioner_name, actions = next(iter(group.items()))
            
            print(f"\n[Группа {index}/{len(actions_pipeline)}] Переключение на актионера: '{actioner_name}'...")
            
            # 1. Меняем актионера на сервере перед отправкой его пачки команд
            if not await self.set_actioner(actioner_name):
                print(f"Ошибка: Не удалось переключить актионер на '{actioner_name}'. Прерывание конвейера.")
                raise RuntimeError(f"Failed to set actioner to '{actioner_name}' during execution pipeline.")
            
            print(f"Актионер '{actioner_name}' успешно установлен. Отправка действий (количество: {len(actions)})...")

            # 2. Формируем payload для /custom_command (старый вариант)
            data_payload = {
                "payload_data": actions
            }
            
            # 3. Выполняем запрос к серверу
            res = await self._post("/custom_command", data=data_payload)
            last_res = res  # Сохраняем последний ответ для финального статуса
            
            # Собираем отчеты воедино
            report = res.get("report")
            if report:
                combined_reports.append({
                    "actioner": actioner_name,
                    "report": report
                })
            
            print(f"Группа {index} успешно выполнена. Статус: {res.get('status')}")

        print("\n--- Все группы действий конвейера обработаны ---\n")

        # Возвращаем структуру, похожую на старый вариант, но с объединенным отчетом
        return {
            "status": "ok" if all(r.get("status") == "ok" for r in [last_res]) else last_res.get("status"),
            "result": last_res.get("result"),
            "actioner": last_res.get("current_actioner"),
            "actioners": last_res.get("actioners"),
            "report": combined_reports  # Теперь здесь список отчетов по каждому актионеру
        }


    # ===================== INTERNAL HTTP =====================

    async def _get(self, path: str) -> Any:
        await self._ensure_client()
        resp = await self._client.get(path)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, data: Dict[str, Any]) -> Any:
        await self._ensure_client()

        # 1. Match the working synchronous double-wrap and hash logic
        payload = {
            "data": data,
            "hash": self._compute_hash(data)
        }

        resp = await self._client.post(path, json=payload)
        resp.raise_for_status()
        resp_json = resp.json()

        # 2. Port the exact server-side verification logic from your working script
        expected_hash = resp_json.get("hash")
        if expected_hash:
            if path == "/sessions":
                data_to_verify = {"sessions": resp_json.get("sessions")}
            elif path == "/gs_cmd":
                data_to_verify = resp_json.get("data", {})
            elif path == "/custom_command":
                data_to_verify = {k: v for k, v in resp_json.items() if k != "hash"}
            else:
                data_to_verify = {}

            if self._compute_hash(data_to_verify) != expected_hash:
                raise ValueError("Client-side error: Server response hash mismatch.")

        return resp_json


    # ===================== HELPERS =====================

    async def _is_initialized(self) -> bool:
        actioners = await self.get_actioners()
        return len(actioners) > 0

    def _resolve_actioner(
        self,
        actioners: List[List[str]],
        target: Optional[str]
    ) -> str:
        if not target:
            return actioners[0][1]

        for a in actioners:
            if a[1].endswith(target):
                return a[1]

        return actioners[0][1]
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Computes SHA-256 hash from canonical JSON (sorted keys, compact separators).
        Matches the server's backend implementation precisely.
        """
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


    def _create_payload( self, cmd_type: str, cmd_value: Any) -> Dict[str, Any]:
        data_payload = {
            "payload_data": {
                "cmd_type": cmd_type,
                "cmd_value": cmd_value
            }
        }
        payload = {
            "data": data_payload,
            "hash": self._compute_hash(data_payload)
        }
        return payload
 
    
