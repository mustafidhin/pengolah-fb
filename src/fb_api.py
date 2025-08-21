import requests
from typing import Dict, Any, List, Optional


class GraphApiError(Exception):
    pass


class FacebookClient:
    def __init__(self, access_token: str, graph_api_version: str = "v19.0") -> None:
        self.access_token = access_token
        self.base_url = f"https://graph.facebook.com/{graph_api_version}"

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        params = dict(params or {})
        params["access_token"] = self.access_token
        try:
            resp = requests.request(method=method.upper(), url=url, params=params, json=json, timeout=30)
        except requests.RequestException as exc:
            raise GraphApiError(str(exc)) from exc

        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = {"error": {"message": resp.text}}
            message = payload.get("error", {}).get("message", resp.text)
            raise GraphApiError(f"HTTP {resp.status_code}: {message}")

        try:
            return resp.json()
        except ValueError:
            raise GraphApiError("Invalid JSON response")

    def get_page_info(self, page_id: str) -> Dict[str, Any]:
        fields = "id,name,link"
        return self._request("GET", f"/{page_id}", params={"fields": fields})

    def get_page_posts(self, page_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        fields = (
            "id,message,created_time,permalink_url,"
            "attachments{media_type,media,url,subattachments},status_type"
        )
        data = self._request("GET", f"/{page_id}/posts", params={"fields": fields, "limit": limit})
        return data.get("data", [])

    def create_page_post(self, page_id: str, message: str, link: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"message": message}
        if link:
            params["link"] = link
        return self._request("POST", f"/{page_id}/feed", params=params)