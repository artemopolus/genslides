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
        timeout: float = 30.0,
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

        if await self._is_initialized():
            return {"status": "already_initialized"}

        sessions = await self.get_sessions()
        if session_name not in sessions:
            raise ValueError(f"Session '{session_name}' not found")

        ok = await self.load_session(session_name)
        if not ok:
            raise RuntimeError("Failed to load session")

        actioners = await self.get_actioners()
        if not actioners:
            raise RuntimeError("No actioners after session load")

        selected = self._resolve_actioner(actioners, actioner_path)

        if not await self.set_actioner(selected):
            raise RuntimeError("Failed to set actioner")

        if not await self.load_exttree_actioner():
            raise RuntimeError("Failed to load ext_tree")

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
        res = await self._get("/sessions")
        return res or []

    async def load_session(self, session_name: str) -> bool:
        res = await self._post("/command", {
            "cmd_type": "load_session",
            "cmd_value": session_name
        })
        return res.get("status") == "ok"

    async def get_actioners(self) -> List[List[str]]:
        res = await self._post("/command", {
            "cmd_type": "get_actioners",
            "cmd_value": ""
        })
        return res.get("data", {}).get("choices", [])

    async def set_actioner(self, actioner_path: str) -> bool:
        res = await self._post("/command", {
            "cmd_type": "set_actioner",
            "cmd_value": actioner_path
        })
        return res.get("status") == "ok"

    async def load_exttree_actioner(self) -> bool:
        res = await self._post("/command", {
            "cmd_type": "load_exttree_actioner",
            "cmd_value": ""
        })
        return res.get("status") == "ok"

    async def set_task(self, actioner: str, task: str) -> bool:
        res = await self._post("/command", {
            "cmd_type": "set_task",
            "cmd_value": {
                "actioner": actioner,
                "task": task
            }
        })
        return res.get("status") == "ok"

    # ===================== INTERNAL HTTP =====================

    async def _get(self, path: str) -> Any:
        await self._ensure_client()
        resp = await self._client.get(path)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        await self._ensure_client()
        resp = await self._client.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()

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
    
