import hashlib
import json
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