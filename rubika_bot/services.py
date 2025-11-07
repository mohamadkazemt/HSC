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
        if not self.token:
            raise ValueError("Rubika bot token is not configured. Please set it in settings.")

    @property
    def _bases(self) -> List[str]:
        # استفاده از چند endpoint برای fallback
        # ترتیب اولویت: ابتدا v3، سپس بدون version
        # api.rubika.ir حذف شد چون DNS resolve نمی‌شود
        return [
            "https://botapi.rubika.ir/v3",
            "https://botapi.rubika.ir",
        ]

    def send_message(self, chat_id: str, text: str, alternatives: Optional[List[str]] = None) -> Dict[str, Any]:
        """ارسال پیام ساده به ربات روبیکا"""
        from .models import WebhookLog
        
        # استفاده از چند URL برای fallback در صورت خطا - مطابق Flask bot
        base_urls = [
            f"https://botapi.rubika.ir/v3/{self.token}/sendMessage",
            f"https://botapi.rubika.ir/{self.token}/sendMessage",
            f"https://api.rubika.ir/v3/{self.token}/sendMessage"  # Flask bot هم این را دارد
        ]
        
        payload = {"chat_id": chat_id, "text": text}
        headers = {"Content-Type": "application/json"}
        
        last_err = None
        
        for url in base_urls:
            try:
                # timeout=20 مطابق Flask bot
                response = requests.post(url, json=payload, headers=headers, timeout=20)
                status = response.status_code
                try:
                    body = response.json()
                except Exception:
                    body = response.text[:300]
                
                # مطابق Flask bot: فقط status code را چک می‌کنیم
                if 200 <= status < 300:
                    WebhookLog.log_outgoing('ارسال موفق', f'پیام به {chat_id} ارسال شد', {
                        'chat_id': chat_id,
                        'url': url,
                        'status': status,
                        'body': body
                    })
                    return {"ok": True, "body": body, "status": status, "url": url}
                
                # اگر INVALID_INPUT بود و alternatives داریم - مطابق Flask bot
                if isinstance(body, dict) and body.get("status") == "INVALID_INPUT" and alternatives:
                    for alt in alternatives:
                        try:
                            resp2 = requests.post(url, json={"chat_id": alt, "text": text}, headers=headers, timeout=20)
                            try:
                                b2 = resp2.json()
                            except Exception:
                                b2 = resp2.text[:300]
                            if 200 <= resp2.status_code < 300 and (not isinstance(b2, dict) or b2.get("status") not in ("INVALID_INPUT", "ERROR")):
                                WebhookLog.log_outgoing('ارسال موفق با alternative', f'پیام با alternative {alt} ارسال شد', {
                                    'chat_id': alt,
                                    'url': url,
                                    'status': resp2.status_code,
                                    'body': b2
                                })
                                return {"ok": True, "body": b2, "status": resp2.status_code, "url": url, "alt": alt}
                        except Exception as ee:
                            WebhookLog.log_error('خطا در تلاش مجدد', f'خطا با alternative {alt}: {str(ee)}')
                            continue
                
                # اگر این URL کار نکرد، به URL بعدی می‌رویم
                WebhookLog.log_warning('ارسال ناموفق', f'Status {status} از {url}', {
                    'status': status,
                    'body': body
                })
                
            except requests.exceptions.Timeout:
                last_err = f"Timeout from {url}"
                WebhookLog.log_error('Timeout', f'Timeout از {url}')
                continue
            except Exception as e:
                error_str = str(e)
                # فیلتر کردن خطاهای DNS برای api.rubika.ir
                if 'api.rubika.ir' in error_str and ('NameResolutionError' in error_str or 'Failed to resolve' in error_str):
                    # این خطا را لاگ نکن چون انتظار می‌رود
                    last_err = e
                    continue
                
                last_err = e
                WebhookLog.log_error('خطا در ارسال', f'خطا از {url}: {str(e)}', {
                    'url': url,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                continue
        
        # اگر همه URL ها ناموفق بودند - مطابق Flask bot: exception نمی‌دهیم، فقط لاگ می‌کنیم
        last_error_str = str(last_err) if last_err else None
        # فیلتر کردن خطاهای DNS برای api.rubika.ir
        if last_error_str and 'api.rubika.ir' in last_error_str and ('NameResolutionError' in last_error_str or 'Failed to resolve' in last_error_str):
            # این خطا را لاگ نکن چون انتظار می‌رود
            pass
        else:
            WebhookLog.log_error('ارسال کاملاً ناموفق', f'نتوانست پیام را به {chat_id} ارسال کند', {
                'chat_id': chat_id,
                'last_error': last_error_str
            })
        
        # مطابق Flask bot: exception نمی‌دهیم، فقط False برمی‌گردانیم
        return {"ok": False, "error": str(last_err) if last_err else "All endpoints failed"}

    def send_message_with_buttons(self, chat_id: str, text: str, rows: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """ارسال پیام با دکمه‌های inline - مطابق Flask bot"""
        # استفاده مستقیم از URL مثل Flask bot
        url = f"https://botapi.rubika.ir/v3/{self.token}/sendMessage"
        formatted_rows = [{"buttons": row} for row in rows]
        payload = {"chat_id": chat_id, "text": text, "inline_keypad": {"rows": formatted_rows}}
        headers = {"Content-Type": "application/json"}
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            st = getattr(r, 'status_code', 200)
            try:
                ok = 200 <= st < 300
            except TypeError:
                ok = True
            if ok:
                try:
                    body = r.json()
                except Exception:
                    body = r.text[:300]
                from .models import WebhookLog
                WebhookLog.log_outgoing('ارسال پیام با دکمه', f'پیام با دکمه به {chat_id} ارسال شد', {
                    'url': url,
                    'status': st,
                    'body': body
                })
                return {"ok": True, "body": body, "status": st}
            else:
                from .models import WebhookLog
                WebhookLog.log_error('ارسال پیام با دکمه ناموفق', f'Status {st} از {url}', {
                    'status': st,
                    'body': r.text[:300] if hasattr(r, 'text') else None
                })
                return {"ok": False, "error": f"Status {st}"}
        except Exception as e:
            from .models import WebhookLog
            WebhookLog.log_error('خطا در ارسال پیام با دکمه', f'خطا از {url}: {str(e)}', {'error': str(e)})
            return {"ok": False, "error": str(e)}

    def answer_query(self, query_id: str, text: str, show_alert: bool = False) -> Dict[str, Any]:
        """پاسخ به کوئری اینلاین کیبورد - مطابق Flask bot"""
        url = f"https://botapi.rubika.ir/v3/{self.token}/answerCallbackQuery"
        payload = {"query_id": query_id, "text": text, "show_alert": show_alert}
        headers = {"Content-Type": "application/json"}
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            st = getattr(r, 'status_code', 200)
            try:
                ok = 200 <= st < 300
            except TypeError:
                ok = True
            if ok:
                try:
                    body = r.json()
                except Exception:
                    body = r.text[:300]
                from .models import WebhookLog
                WebhookLog.log_outgoing('پاسخ کوئری', f'پاسخ کوئری {query_id} ارسال شد', {
                    'query_id': query_id,
                    'status': st,
                    'body': body
                })
                return {"ok": True, "body": body, "status": st}
            else:
                from .models import WebhookLog
                WebhookLog.log_error('پاسخ کوئری ناموفق', f'Status {st} از {url}', {
                    'query_id': query_id,
                    'status': st
                })
                return {"ok": False, "error": f"Status {st}"}
        except Exception as e:
            from .models import WebhookLog
            WebhookLog.log_error('خطا در پاسخ کوئری', f'خطا از {url}: {str(e)}', {'error': str(e)})
            return {"ok": False, "error": str(e)}

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
        """دریافت اطلاعات webhook فعلی از API روبیکا"""
        last_error = None
        # استفاده مستقیم از URLs معتبر (بدون api.rubika.ir)
        urls = [
            f"https://botapi.rubika.ir/v3/{self.token}/getBotEndpoint",
            f"https://botapi.rubika.ir/{self.token}/getBotEndpoint",
        ]
        
        for url in urls:
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        # بررسی اینکه پاسخ معتبر است
                        if isinstance(data, dict):
                            return data
                        else:
                            last_error = f"Invalid response format from {url}"
                            continue
                    except ValueError:
                        last_error = f"JSON decode error from {url}: {r.text[:200]}"
                        continue
                else:
                    last_error = f"HTTP {r.status_code} from {url}: {r.text[:200]}"
                    continue
            except requests.exceptions.Timeout:
                last_error = f"Timeout from {url}"
                continue
            except requests.exceptions.RequestException as e:
                # فیلتر کردن خطاهای DNS که غیرضروری هستند
                error_str = str(e)
                if 'NameResolutionError' in error_str or 'Failed to resolve' in error_str or 'api.rubika.ir' in error_str:
                    # این خطا را نادیده بگیریم چون endpoint در دسترس نیست
                    continue
                last_error = f"Request error from {url}: {error_str}"
                continue
            except Exception as e:
                error_str = str(e)
                if 'NameResolutionError' in error_str or 'Failed to resolve' in error_str or 'api.rubika.ir' in error_str:
                    continue
                last_error = f"Unexpected error from {url}: {error_str}"
                continue
        return {"ok": False, "error": last_error or "All endpoints failed"}
