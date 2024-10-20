import requests
import time
import urllib3
import os
import logging
import asyncio
from dotenv import load_dotenv
from logger import TelegramLogger, setup_logger
from colorama import Fore, Style, init
from datetime import datetime, timedelta

init(autoreset=True)

# Ignore InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write("# This file contains environment variables.\n")

load_dotenv()

def prompt_for_env_variables():
    inputs = []

    token = os.getenv("TOKEN")
    if not token:
        token = input("Please enter your Dawn Token: ")
        inputs.append(f"TOKEN={token}")

    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        telegram_token = input("Please enter your Telegram Bot Token: ")
        inputs.append(f"TELEGRAM_TOKEN={telegram_token}")

    chat_id = os.getenv("CHAT_ID")
    if not chat_id:
        chat_id = input("Please enter your Chat ID: ")
        inputs.append(f"CHAT_ID={chat_id}")

    with open('.env', 'a') as f:
        for item in inputs:
            f.write(f"{item}\n")

    return token, telegram_token, chat_id

TOKEN, TELEGRAM_TOKEN, CHAT_ID = prompt_for_env_variables()

telegram_logger = TelegramLogger(TELEGRAM_TOKEN, CHAT_ID)
setup_logger(telegram_logger)

POINTS_URL = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
PING_URL = "https://www.aeropres.in/dawnserver/ping"
KEEPALIVE_URL = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"

def create_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

email = ""

# Function to fetch points
async def fetch_points(headers):
    global email
    try:
        response = requests.get(POINTS_URL, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json().get("data", {}).get("rewardPoint", {})
        email = data.get('userId','')

        total_points = sum([
            data.get('points', 0),
            data.get('twitter_x_id_points', 0),
            data.get('discordid_points', 0),
            data.get('telegramid_points', 0)
        ])

        log_message = (
            f"{'ID'.ljust(15)}: {data.get('_id')}\n"
            f"{'User'.ljust(15)}: {email}\n"
            f"{'Total Points'.ljust(15)}: {total_points}\n"
        )

        logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Fetching points...\n{Fore.YELLOW}{log_message}")
        await telegram_logger.send_message(log_message)
        return total_points

    except requests.exceptions.RequestException as e:
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error fetching points: {e}")
        await telegram_logger.send_message(f"Error fetching points: {e}")
        return 0 

async def ping_server(headers):
    try:
        response = requests.get(PING_URL, headers=headers, verify=False)
        response.raise_for_status()
        logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Ping successful. Server response: {response.text}")
        await telegram_logger.send_message(f"Ping successful. Server response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Ping failed: {e}")
        await telegram_logger.send_message(f"Ping failed: {e}")

async def keep_alive(headers, last_keepalive_log_time):
    try:
        response = requests.post(KEEPALIVE_URL, headers=headers, json={
            "username": email,
            "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
            "numberoftabs": 0,
            "_v": "1.0.9"
        }, verify=False, timeout=30)

        if response.status_code == 200:
            logging.info(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Keepalive successful.")
            current_time = datetime.now()
            if current_time - last_keepalive_log_time >= timedelta(minutes=5):
                await telegram_logger.send_message("Keepalive successful.")
                last_keepalive_log_time = current_time
        else:
            logging.warning(f"{Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Keepalive returned status code {response.status_code}")
            await telegram_logger.send_message(f"Keepalive returned status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Keepalive failed: {e}")
        await telegram_logger.send_message(f"Keepalive failed: {e}")

# Main execution flow
async def main():
    logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
    headers = create_headers(TOKEN)

    last_keepalive_log_time = datetime.now() - timedelta(minutes=5)
    while True:
        await ping_server(headers)
        await keep_alive(headers, last_keepalive_log_time) 
        await fetch_points(headers)
        await asyncio.sleep(500)

if __name__ == "__main__":
    asyncio.run(main())


### Thanks to @rainlovy99 for methode
