import logging
import asyncio
import aiohttp

class TelegramLogger:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    async def send_message(self, message):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    def start(self):
        pass

def setup_logger(telegram_logger):
    logging.basicConfig(level=logging.INFO)

    class TelegramHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            loop = asyncio.get_event_loop()
            loop.create_task(telegram_logger.send_message(msg))  # Schedule the message to be sent

    logger = logging.getLogger()
    logger.addHandler(TelegramHandler())
