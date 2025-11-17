import logging
from core.sms_service import send_template_sms

logger = logging.getLogger(__name__)

RUBIKA_CONNECTION_TEMPLATE = 920200

def send_connection_code_sms(mobile_number, connection_code):
    """ارسال کد اتصال روبیکا از طریق SMS با استفاده از سرویس مرکزی."""
    try:
        from rubika_bot.models import RubikaBotSettings
        from rubika_bot.shortener import create_short_link
        bot_settings = RubikaBotSettings.get_solo()
        bot_username = bot_settings.bot_username or "YourBot"
        short_link = create_short_link(connection_code, bot_username)
        parameters = [{"Name": "LINK", "Value": short_link}]
        return send_template_sms(mobile_number, RUBIKA_CONNECTION_TEMPLATE, parameters)
    except Exception as e:
        logger.exception(f"💥 خطا در ارسال کد اتصال: {e}")
        return False
