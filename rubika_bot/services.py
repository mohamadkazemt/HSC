import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from .models import RubikaBotSettings


@dataclass
class RubikaClient:
    token: Optional[str] = None

    def __post_init__(self):
        s = RubikaBotSettings.get_solo()
        self.token = self.token or s.token

    @property
    def _bases(self) -> List[str]:
        # Try multiple base endpoints like the working Flask bot
        return [
            "https://botapi.rubika.ir/v3",
            "https://botapi.rubika.ir",
            "https://api.rubika.ir/v3",
        ]

    def send_message(self, chat_id: str, text: str, alternatives: Optional[List[str]] = None) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "text": text}
        last_exc = None
        for b in self._bases:
            url = f"{b}/{self.token}/sendMessage"
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
                try:
                    body = r.json()
                except Exception:
                    body = {"raw": r.text[:300]}
                status = getattr(r, 'status_code', 200)
                try:
                    ok_status = 200 <= status < 300
                except TypeError:
                    ok_status = True
                if ok_status:
                    return {"ok": True, "body": body, "status": status, "url": url}
                # fallback to alternatives if INVALID_INPUT
                if isinstance(body, dict) and body.get("status") == "INVALID_INPUT" and alternatives:
                    for alt in alternatives:
                        r2 = requests.post(url, json={"chat_id": alt, "text": text}, headers={"Content-Type": "application/json"}, timeout=20)
                        try:
                            b2 = r2.json()
                        except Exception:
                            b2 = {"raw": r2.text[:300]}
                        st2 = getattr(r2, 'status_code', 200)
                        try:
                            ok2 = 200 <= st2 < 300
                        except TypeError:
                            ok2 = True
                        if ok2 and (not isinstance(b2, dict) or b2.get("status") not in ("INVALID_INPUT", "ERROR")):
                            return {"ok": True, "body": b2, "status": st2, "url": url, "alt": alt}
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        return {"ok": False}

    def send_message_with_buttons(self, chat_id: str, text: str, rows: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "text": text, "inline_keypad": {"rows": [{"buttons": row} for row in rows]}}
        last_exc = None
        for b in self._bases:
            url = f"{b}/{self.token}/sendMessage"
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
                st = getattr(r, 'status_code', 200)
                try:
                    ok = 200 <= st < 300
                except TypeError:
                    ok = True
                if ok:
                    try:
                        return r.json()
                    except Exception:
                        return {"ok": True, "status": st}
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        return {"ok": False}

    def answer_query(self, query_id: str, text: str, show_alert: bool = False) -> Dict[str, Any]:
        payload = {"query_id": query_id, "text": text, "show_alert": show_alert}
        for b in self._bases:
            url = f"{b}/{self.token}/answerCallbackQuery"
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            st = getattr(r, 'status_code', 200)
            try:
                ok = 200 <= st < 300
            except TypeError:
                ok = True
            if ok:
                try:
                    return r.json()
                except Exception:
                    return {"ok": True, "status": st}
        return {"ok": False}

    def update_bot_endpoints(self, webhook_url: str, update_types: Optional[List[str]] = None) -> Dict[str, Any]:
        update_types = update_types or [
            "ReceiveUpdate",
            "ReceiveInlineMessage",
            "ReceiveQuery",
            "GetSelectionItem",
            "SearchSelectionItems",
        ]
        results = {}
        for b in self._bases:
            endpoint = f"{b}/{self.token}/updateBotEndpoints"
            ok = True
            partial = {}
            for t in update_types:
                try:
                    r = requests.post(endpoint, json={"type": t, "url": webhook_url}, headers={"Content-Type": "application/json"}, timeout=30)
                    try:
                        body = r.json()
                    except Exception:
                        body = {"raw": r.text[:300]}
                    partial[t] = {"status": getattr(r, 'status_code', None), "body": body}
                    if body.get("status") != "ok":
                        ok = False
                except Exception as e:
                    partial[t] = {"error": str(e)}
                    ok = False
            results[endpoint] = {"ok": ok, "details": partial}
            if ok:
                return {"ok": True, "endpoint": endpoint, "details": partial}
        # Fallback: try single camelCase endpoint with combined payload
        # e.g., updateBotEndpoint with keys receiveUpdate, receiveInlineMessage, ...
        for b in self._bases:
            endpoint = f"{b}/{self.token}/updateBotEndpoint"
            payload = {}
            mapping = {
                "ReceiveUpdate": "receiveUpdate",
                "ReceiveInlineMessage": "receiveInlineMessage",
                "ReceiveQuery": "receiveQuery",
                "GetSelectionItem": "getSelectionItem",
                "SearchSelectionItems": "searchSelectionItems",
            }
            for t in update_types:
                key = mapping.get(t)
                if key:
                    payload[key] = webhook_url
            try:
                r = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                try:
                    body = r.json()
                except Exception:
                    body = {"raw": r.text[:300]}
                st = getattr(r, 'status_code', 200)
                ok = isinstance(body, dict) and body.get('status') == 'ok'
                if ok:
                    return {"ok": True, "endpoint": endpoint, "body": body, "status": st}
            except Exception:
                pass
        return {"ok": False, "results": results}

    def get_bot_endpoint(self) -> Dict[str, Any]:
        for b in self._bases:
            url = f"{b}/{self.token}/getBotEndpoint"
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                return r.json()
            except Exception:
                continue
        return {"ok": False}
