import re
from typing import Any, Dict, List, Optional

import requests


LIBRARY_ID_RE = re.compile(r"^/[^/]+/[^/]+(/[^/]+)?$")


class Context7Client:
    """
    Minimal Context7 HTTP client with:
      - GET /v2/libs/search  -> search(library_name, query)
      - GET /v2/context      -> get_context(library_id, query, type_)

    Notes:
      - This client defaults get_context `type_` to 'json' to return structured data.
      - If you prefer raw text set type_='txt'.
    """

    def __init__(
        self,
        base_url: str = "https://context7.com/api",
        api_key: Optional[str] = None,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _parse_json_or_text(self, resp: requests.Response) -> Any:
        """Return parsed JSON when possible, otherwise raw text."""
        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _raise_for_non_ok(self, resp: requests.Response) -> None:
        """
        Raises HTTPError with helpful body when response status is not 2xx.
        Special-cases a few documented statuses to surface their JSON bodies.
        """
        if 200 <= resp.status_code < 300:
            return

        body = self._parse_json_or_text(resp)
        # Attach the parsed body to the HTTPError message for easier debugging
        raise requests.HTTPError(f"{resp.status_code} Error: {body}")

    # ----------------------
    # Search endpoint
    # ----------------------
    def search(self, library_name: str, query: str) -> List[Dict]:
        """
        GET /v2/libs/search?libraryName=<>&query=<>

        Returns list of library objects (may be empty).
        """
        if not library_name:
            raise ValueError("library_name is required")
        if not query:
            raise ValueError("query is required")

        url = f"{self.base_url}/v2/libs/search"
        resp = self.session.get(url, params={"libraryName": library_name, "query": query}, timeout=self.timeout)
        self._raise_for_non_ok(resp)
        data = self._parse_json_or_text(resp)
        # OpenAPI shape: { results: [ ... ] }
        if isinstance(data, dict):
            return data.get("results", [])
        return []

    # ----------------------
    # Context endpoint
    # ----------------------
    def get_context(self, library_id: str, query: str, type_: str = "json") -> Dict:
        """
        GET /v2/context?libraryId=<>&query=<>&type=(json|txt)

        Returns parsed JSON when type_ == 'json'. If server returns text for 'txt',
        the returned value may be a string.
        """
        if not library_id:
            raise ValueError("library_id is required")
        if not LIBRARY_ID_RE.match(library_id):
            raise ValueError("library_id must match pattern '/owner/repo' or '/owner/repo/version'")

        if not query:
            raise ValueError("query is required")

        if type_ not in ("json", "txt"):
            raise ValueError("type_ must be 'json' or 'txt'")

        url = f"{self.base_url}/v2/context"
        params = {"libraryId": library_id, "query": query, "type": type_}
        resp = self.session.get(url, params=params, timeout=self.timeout)

        # Handle known special statuses gracefully so we can show the body
        if resp.status_code == 301:
            # Expect JSON with redirectUrl per spec
            body = self._parse_json_or_text(resp)
            raise requests.HTTPError(f"301 Moved Permanently: {body}")
        if resp.status_code == 202:
            body = self._parse_json_or_text(resp)
            raise requests.HTTPError(f"202 Accepted: {body}")

        self._raise_for_non_ok(resp)
        return self._parse_json_or_text(resp)
