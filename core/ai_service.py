# core/ai_service.py
"""
سرویس هوش مصنوعی برای خودکارسازی کارها در سیستم HSE
از APIهای مختلف هوش مصنوعی پشتیبانی می‌کند
"""
import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIService:
    """
    سرویس اصلی برای ارتباط با APIهای هوش مصنوعی
    از OpenAI API یا APIهای مشابه پشتیبانی می‌کند
    """
    
    def __init__(self, use_db_settings: bool = True):
        """
        Args:
            use_db_settings: اگر True باشد، از تنظیمات دیتابیس استفاده می‌کند
        """
        if use_db_settings:
            try:
                from .ai_models import AISettings
                ai_settings = AISettings.get_solo()
                if ai_settings.is_active:
                    self.api_key = ai_settings.get_api_key_safe() or ''
                    self.api_base_url = ai_settings.api_base_url or ai_settings.get_default_api_base_url()
                    self.model = ai_settings.model
                    self.provider = ai_settings.provider
                    self.timeout = ai_settings.timeout
                    self.max_retries = ai_settings.max_retries
                    self.cache_timeout = ai_settings.cache_timeout
                    self.temperature = ai_settings.temperature
                else:
                    # اگر غیرفعال است، از تنظیمات پیش‌فرض استفاده کن
                    self._load_from_env()
            except Exception as e:
                logger.warning(f"خطا در بارگذاری تنظیمات از دیتابیس: {e}")
                self._load_from_env()
        else:
            self._load_from_env()
        
        # ایجاد session با retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _load_from_env(self):
        """بارگذاری تنظیمات از environment variables"""
        self.api_key = getattr(settings, 'AI_API_KEY', os.environ.get('AI_API_KEY', ''))
        self.api_base_url = getattr(settings, 'AI_API_BASE_URL', os.environ.get('AI_API_BASE_URL', 'https://api.openai.com/v1'))
        self.model = getattr(settings, 'AI_MODEL', os.environ.get('AI_MODEL', 'gpt-4'))
        self.provider = getattr(settings, 'AI_PROVIDER', os.environ.get('AI_PROVIDER', 'openai'))
        self.timeout = getattr(settings, 'AI_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)
        self.cache_timeout = getattr(settings, 'AI_CACHE_TIMEOUT', 3600)
        self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
        
    def _get_cache_key(self, prompt: str, context: Dict = None) -> str:
        """ایجاد کلید کش برای درخواست"""
        import hashlib
        cache_data = json.dumps({'prompt': prompt, 'context': context or {}}, sort_keys=True)
        return f'ai_cache_{hashlib.md5(cache_data.encode()).hexdigest()}'
    
    def _call_openai_api(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """فراخوانی OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 2000,
        }
        
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f'{self.api_base_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=(15, self.timeout),
                    verify=True
                )
                response.raise_for_status()
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            except requests.exceptions.SSLError as ssl_error:
                logger.warning(f"SSL Error (attempt {attempt + 1}/{max_retries}): {str(ssl_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"SSL Error after {max_retries} attempts: {str(ssl_error)}")
                    return None
            except requests.exceptions.Timeout as timeout_error:
                logger.warning(f"Timeout Error (attempt {attempt + 1}/{max_retries}): {str(timeout_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {str(timeout_error)}")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"خطا در فراخوانی OpenAI API: {e}")
                    return None
    
    def _call_anthropic_api(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """فراخوانی Anthropic Claude API"""
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        # تبدیل فرمت پیام‌ها برای Anthropic
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                conversation_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        data = {
            'model': self.model,
            'messages': conversation_messages,
            'temperature': temperature,
            'max_tokens': 2000,
        }
        
        if system_message:
            data['system'] = system_message
        
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f'{self.api_base_url}/messages',
                    headers=headers,
                    json=data,
                    timeout=(15, self.timeout),
                    verify=True
                )
                response.raise_for_status()
                result = response.json()
                return result.get('content', [{}])[0].get('text', '')
            except requests.exceptions.SSLError as ssl_error:
                logger.warning(f"SSL Error (attempt {attempt + 1}/{max_retries}): {str(ssl_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"SSL Error after {max_retries} attempts: {str(ssl_error)}")
                    return None
            except requests.exceptions.Timeout as timeout_error:
                logger.warning(f"Timeout Error (attempt {attempt + 1}/{max_retries}): {str(timeout_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {str(timeout_error)}")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"خطا در فراخوانی Anthropic API: {e}")
                    return None
    
    def _call_google_api(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """فراخوانی Google AI Studio (Gemini) API"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        # تبدیل پیام‌ها به فرمت Gemini
        # ترکیب system prompt و user prompt در یک پیام (مطابق کد نمونه)
        system_instruction = None
        user_prompt = ""
        
        for msg in messages:
            if msg['role'] == 'system':
                system_instruction = msg['content']
            elif msg['role'] == 'user':
                if user_prompt:
                    user_prompt += "\n\n" + msg['content']
                else:
                    user_prompt = msg['content']
        
        # ساخت درخواست مطابق با فرمت Google
        # طبق کد نمونه، system prompt و user prompt را در یک parts قرار می‌دهیم
        combined_text = f"{system_instruction}\n\n{user_prompt}" if system_instruction else user_prompt
        
        data = {
            'contents': [{
                'parts': [{'text': combined_text}]
            }],
            'generationConfig': {
                'temperature': temperature,
                'topP': 0.95,
                'topK': 40,
                'maxOutputTokens': 8192,
            }
        }
        
        # استفاده از مدل بدون prefix models/ در صورت وجود
        model_name = self.model
        if not model_name.startswith('models/'):
            model_name = f'models/{model_name}'
        
        # استفاده از query parameter برای API key (مطابق کد نمونه)
        url = f'{self.api_base_url}/{model_name}:generateContent?key={self.api_key}'
        
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=(15, 60),  # (connect timeout: 15s, read timeout: 60s)
                    verify=True
                )
                
                # بررسی status code قبل از raise_for_status
                if response.status_code == 429:
                    error_detail = ""
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('error', {}).get('message', '')
                    except:
                        error_detail = response.text[:200]
                    error_msg = f"Too Many Requests (429) - {error_detail}"
                    logger.error(f"خطا در فراخوانی Google AI API: {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"محدودیت quota/rate limit: {error_detail}")
                
                response.raise_for_status()
                result = response.json()
                
                # استخراج متن از پاسخ Gemini
                candidates = result.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                
                # بررسی safety ratings
                if candidates and 'safetyRatings' in candidates[0]:
                    safety_ratings = candidates[0].get('safetyRatings', [])
                    blocked = any(rating.get('blocked', False) for rating in safety_ratings)
                    if blocked:
                        logger.warning("پاسخ توسط Google AI به دلیل safety ratings مسدود شد")
                        return None
                
                return None
                
            except requests.exceptions.SSLError as ssl_error:
                logger.warning(f"SSL Error (attempt {attempt + 1}/{max_retries}): {str(ssl_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"SSL Error after {max_retries} attempts: {str(ssl_error)}")
                    raise Exception(f"خطا در اتصال SSL به Google AI: {str(ssl_error)}")
            except requests.exceptions.Timeout as timeout_error:
                logger.warning(f"Timeout Error (attempt {attempt + 1}/{max_retries}): {str(timeout_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {str(timeout_error)}")
                    raise Exception(f"خطا در timeout اتصال به Google AI: {str(timeout_error)}")
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 400:
                    error_detail = ""
                    try:
                        error_json = e.response.json()
                        error_detail = error_json.get('error', {}).get('message', '')
                    except:
                        error_detail = e.response.text[:200] if e.response else str(e)
                    if attempt < max_retries - 1:
                        logger.warning(f"Bad Request (attempt {attempt + 1}/{max_retries}): {error_detail}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"درخواست نامعتبر: {error_detail}")
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"HTTP Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise
            except requests.exceptions.RequestException as req_error:
                logger.warning(f"Request Error (attempt {attempt + 1}/{max_retries}): {str(req_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"Request Error after {max_retries} attempts: {str(req_error)}")
                    raise Exception(f"خطا در درخواست به Google AI: {str(req_error)}")
            except Exception as e:
                # برای خطاهای دیگر که از خودمان raise کردیم
                if attempt < max_retries - 1 and 'quota' not in str(e).lower() and '429' not in str(e):
                    logger.warning(f"Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise
    
    def _call_local_api(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """فراخوانی API محلی (مثل Ollama)"""
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'stream': False,
        }
        
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f'{self.api_base_url}/chat/completions',
                    json=data,
                    timeout=(15, self.timeout),
                    verify=False  # برای local API معمولاً SSL نداریم
                )
                response.raise_for_status()
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            except requests.exceptions.Timeout as timeout_error:
                logger.warning(f"Timeout Error (attempt {attempt + 1}/{max_retries}): {str(timeout_error)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {str(timeout_error)}")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"خطا در فراخوانی Local API: {e}")
                    return None
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: str = None,
        context: Dict = None,
        temperature: float = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        تولید متن با استفاده از AI
        
        Args:
            prompt: متن درخواست
            system_prompt: دستورالعمل سیستم (اختیاری)
            context: اطلاعات اضافی برای درخواست
            temperature: میزان خلاقیت (0-1)
            use_cache: استفاده از کش یا نه
        
        Returns:
            متن تولید شده یا None در صورت خطا
        """
        if not self.api_key and self.provider != 'local':
            logger.warning("API Key تنظیم نشده است")
            return None
        
        # بررسی کش
        if use_cache:
            cache_key = self._get_cache_key(prompt, context)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("نتیجه از کش بازگردانده شد")
                return cached_result
        
        # ساخت پیام‌ها
        messages = []
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        # افزودن context به prompt
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            full_prompt = f"{prompt}\n\nاطلاعات اضافی:\n{context_str}"
        
        messages.append({
            'role': 'user',
            'content': full_prompt
        })
        
        # استفاده از temperature از تنظیمات در صورت عدم تعیین
        if temperature is None:
            temperature = getattr(self, 'temperature', 0.7)
        
        # فراخوانی API بر اساس provider
        result = None
        if self.provider == 'openai':
            result = self._call_openai_api(messages, temperature)
        elif self.provider == 'anthropic':
            result = self._call_anthropic_api(messages, temperature)
        elif self.provider == 'google':
            result = self._call_google_api(messages, temperature)
        elif self.provider == 'local':
            result = self._call_local_api(messages, temperature)
        else:
            logger.error(f"Provider نامعتبر: {self.provider}")
            return None
        
        # ذخیره در کش
        if result and use_cache:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: str = None,
        context: Dict = None,
        temperature: float = None
    ) -> Optional[Dict]:
        """
        تولید JSON با استفاده از AI
        
        Returns:
            دیکشنری Python یا None در صورت خطا
        """
        json_prompt = f"{prompt}\n\nلطفاً پاسخ را به صورت JSON معتبر برگردانید."
        
        if not system_prompt:
            system_prompt = "شما یک دستیار هوشمند هستید که پاسخ‌ها را به صورت JSON معتبر برمی‌گردانید."
        
        # استفاده از temperature پایین‌تر برای JSON
        if temperature is None:
            temperature = 0.3
        
        result = self.generate_text(
            prompt=json_prompt,
            system_prompt=system_prompt,
            context=context,
            temperature=temperature
        )
        
        if not result:
            return None
        
        try:
            # تلاش برای استخراج JSON از پاسخ
            # ممکن است AI پاسخ را با markdown code block برگرداند
            if '```json' in result:
                start = result.find('```json') + 7
                end = result.find('```', start)
                result = result[start:end].strip()
            elif '```' in result:
                start = result.find('```') + 3
                end = result.find('```', start)
                result = result[start:end].strip()
            
            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"خطا در پارس JSON: {e}\nپاسخ: {result}")
            return None


# Singleton instance
_ai_service_instance = None

def get_ai_service(use_db_settings: bool = True) -> AIService:
    """دریافت instance سرویس AI (Singleton)"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService(use_db_settings=use_db_settings)
    return _ai_service_instance

def test_ai_connection() -> Dict[str, Any]:
    """
    تست اتصال به API AI
    
    Returns:
        دیکشنری شامل success, message, و جزئیات
    """
    try:
        ai_service = AIService(use_db_settings=True)
        
        if not ai_service.api_key and ai_service.provider != 'local':
            return {
                'success': False,
                'message': 'API Key تنظیم نشده است. لطفاً API Key را از تنظیمات وارد کنید.',
                'details': {
                    'provider': ai_service.provider,
                    'model': ai_service.model
                }
            }
        
        # تست ساده با یک prompt کوتاه
        test_prompt = "سلام"
        result = ai_service.generate_text(
            prompt=test_prompt,
            system_prompt="شما یک دستیار ساده هستید. فقط یک کلمه پاسخ دهید.",
            temperature=0.1,
            use_cache=False
        )
        
        if result:
            return {
                'success': True,
                'message': 'اتصال موفق بود',
                'details': {
                    'provider': ai_service.provider,
                    'model': ai_service.model,
                    'test_response': result[:100]  # فقط 100 کاراکتر اول
                }
            }
        else:
            return {
                'success': False,
                'message': 'پاسخی از API دریافت نشد. لطفاً تنظیمات را بررسی کنید.',
                'details': {
                    'provider': ai_service.provider,
                    'model': ai_service.model
                }
            }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"خطا در تست اتصال AI: {error_msg}", exc_info=True)
        
        # پیام‌های خاص برای خطاهای رایج
        if 'quota' in error_msg.lower() or '429' in error_msg or 'rate limit' in error_msg.lower():
            message = 'محدودیت quota یا rate limit: شما از سهمیه API خود استفاده کرده‌اید. لطفاً به https://ai.dev/usage مراجعه کنید یا چند لحظه صبر کنید.'
        elif 'api key' in error_msg.lower() or '401' in error_msg or '403' in error_msg:
            message = 'API Key نامعتبر است. لطفاً API Key را از https://aistudio.google.com/ دریافت و وارد کنید.'
        elif '400' in error_msg or 'bad request' in error_msg.lower():
            message = f'درخواست نامعتبر: {error_msg}'
        else:
            message = f'خطا: {error_msg}'
        
        return {
            'success': False,
            'message': message,
            'details': {
                'provider': ai_service.provider if 'ai_service' in locals() else 'unknown',
                'model': ai_service.model if 'ai_service' in locals() else 'unknown',
                'error': error_msg
            }
        }
