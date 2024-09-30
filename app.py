import requests
import time
import urllib3
import os
import logging
import asyncio
from dotenv import load_dotenv
from logger import TelegramLogger, setup_logger
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Ignore InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Check if .env file exists; create it if it doesn't
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write("# This file contains environment variables.\n")

# Load environment variables from the .env file
load_dotenv()

# Function to prompt user for input if .env variables are missing
def prompt_for_env_variables():
    inputs = []

    # Prompt for TOKEN
    token = os.getenv("TOKEN")
    if not token:
        token = input("Please enter your Dawn Token: ")
        inputs.append(f"TOKEN={token}")

    # Prompt for TELEGRAM_TOKEN
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        telegram_token = input("Please enter your Telegram Token: ")
        inputs.append(f"TELEGRAM_TOKEN={telegram_token}")

    # Prompt for CHAT_ID
    chat_id = os.getenv("CHAT_ID")
    if not chat_id:
        chat_id = input("Please enter your Chat ID: ")
        inputs.append(f"CHAT_ID={chat_id}")

    # Write to .env file
    with open('.env', 'a') as f:
        for item in inputs:
            f.write(f"{item}\n")

    return token, telegram_token, chat_id

# Prompt for environment variables
TOKEN, TELEGRAM_TOKEN, CHAT_ID = prompt_for_env_variables()

# Initialize Telegram logger
telegram_logger = TelegramLogger(TELEGRAM_TOKEN, CHAT_ID)
setup_logger(telegram_logger)

# Request URLs
POINTS_URL = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
PING_URL = "https://www.aeropres.in/dawnserver/ping"

# Function to set up headers
def create_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

# Function to fetch points
async def fetch_points(headers):
    try:
        response = requests.get(POINTS_URL, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json().get("data", {}).get("rewardPoint", {})

        total_points = sum([
            data.get('points', 0),
            data.get('twitter_x_id_points', 0),
            data.get('discordid_points', 0),
            data.get('telegramid_points', 0)
        ])

        log_message = (
            f"{'ID'.ljust(15)}: {data.get('_id')}\n"
            f"{'User'.ljust(15)}: {data.get('userId')}\n"
            f"{'Total Points'.ljust(15)}: {total_points}\n"
        )

        # Log to console with color and timestamp
        logging.info(f"\n{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Fetching points...\n{Fore.YELLOW}{log_message}")

        # Send log message to Telegram
        await telegram_logger.send_message("Fetching points: \n" + log_message)

        return total_points  # Return total points for later use

    except requests.exceptions.RequestException as e:
        logging.error(f"\n{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error fetching points: {e}")
        # Send error message to Telegram
        await telegram_logger.send_message(f"Error fetching points: {e}")
        return 0  # Return 0 points on error

# Function to ping the server
async def ping_server(headers):
    try:
        response = requests.get(PING_URL, headers=headers, verify=False)
        response.raise_for_status()
        logging.info(f"\n{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Ping successful. \nServer response: \n{response.text}")
        # Send success message to Telegram
        await telegram_logger.send_message(f"Ping successful. Server response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"\n{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Ping failed: {e}")
        # Send error message to Telegram
        await telegram_logger.send_message(f"Ping failed: {e}")

# Main execution flow
async def main():
    logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
    headers = create_headers(TOKEN)

    while True:
        await fetch_points(headers)
        await ping_server(headers)
        await asyncio.sleep(500)  # Delay before the next loop iteration

if __name__ == "__main__":
    asyncio.run(main())
