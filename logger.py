import logging
import asyncio
import aiohttp

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
            'text': message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        # Log if there's an issue sending the message
                        logging.error(f"Failed to send message to Telegram. Status: {response.status}, Response: {await response.text()}")
                    else:
                        return await response.json()
        
        except aiohttp.ClientError as e:
            # Handle network errors
            logging.error(f"Network error while sending message to Telegram: {str(e)}")
        
        except Exception as e:
            # General exception handler
            logging.error(f"Unexpected error while sending message to Telegram: {str(e)}")

    def start(self):
        pass

def setup_logger(telegram_logger):
    logger = logging.getLogger()

    # Set up console handler to show info-level messages in the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add console handler if it's not already added
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        logger.addHandler(console_handler)

    # Set up Telegram handler to only send error-level messages to Telegram
    class TelegramHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:  # Only send messages with level ERROR or higher
                msg = self.format(record)
                loop = asyncio.get_event_loop()
                loop.create_task(telegram_logger.send_message(msg))  # Send message asynchronously

    telegram_handler = TelegramHandler()
    telegram_handler.setLevel(logging.ERROR)  # Only log errors and above for Telegram
    logger.addHandler(telegram_handler)

    logger.setLevel(logging.DEBUG)  # Set overall logging level (can be adjusted)
