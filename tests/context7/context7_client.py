import requests
from typing import Any, Dict, List, Optional


class Context7Client:
    """
    Minimal Context7 HTTP client for the OpenAPI /v2/libs/search endpoint.

    Usage: client.search(library_name="react", query="state with hooks")
    """

    def __init__(self, base_url: str = "https://context7.com/api", api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if api_key:
            # spec suggests bearer tokens (prefix ctx7sk)
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _handle_response(self, resp: requests.Response) -> Any:
        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()  # will raise HTTPError with text content
        if resp.ok:
            return data
        # Non-2xx: raise with body if present for easier debugging
        message = data if isinstance(data, dict) else resp.text
        http_err = requests.HTTPError(f"{resp.status_code} Error: {message}")
        raise http_err

    def search(self, library_name: str, query: str) -> List[Dict]:
        """
        Call GET /v2/libs/search?libraryName=<>&query=<>

        Returns list of library objects (may be empty).
        """
        if not library_name:
            raise ValueError("library_name is required")
        if not query:
            raise ValueError("query is required")

        url = f"{self.base_url}/v2/libs/search"
        params = {"libraryName": library_name, "query": query}
        resp = self.session.get(url, params=params, timeout=self.timeout)
        data = self._handle_response(resp)
        # According to OpenAPI, response shape is { results: [ ... ] }
        return data.get("results", [])
