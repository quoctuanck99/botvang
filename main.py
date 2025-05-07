import requests
from bs4 import BeautifulSoup
import traceback
from telegram.ext import Updater, CommandHandler
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# Telegram channel ID (e.g., @YourChannelName)
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

INTERVAL = os.environ.get("INTERVAL", 3600)
# Store previous prices to detect changes
previous_prices = {
    'Bao Tin Manh Hai': None,
    'Bao Tin Minh Chau': None
}

# Store website URLs
source_urls = {
    'Bao Tin Manh Hai': "https://www.baotinmanhhai.vn",
    'Bao Tin Minh Chau': "https://btmc.vn"
}


def format_price(price, is_btmc=False):
    """Format price to VND with dots at thousand level"""
    try:
        price_num = int(''.join(filter(str.isdigit, price)))
        if is_btmc:
            price_num *= 1000
        return f"{price_num:,}".replace(",", ".")
    except ValueError:
        return price


def scrape_gold_prices_btmh(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='gold-table-content')

        if not table:
            print("Could not find gold prices table for BTMH")
            return []

        gold_prices = []
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                gold_prices.append({
                    'type': cells[0].text.strip(),
                    'buy_price': format_price(cells[1].text.strip().replace('.', '').split()[0]),
                    'sell_price': format_price(cells[2].text.strip().replace('.', '').split()[0])
                })
                break

        return gold_prices

    except requests.RequestException as e:
        print(f"Error fetching BTMH webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing BTMH data: {e} {traceback.format_exc()}")
        return []


def scrape_btmc_gold_prices(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='bd_price_home')

        if not table:
            print("Could not find gold prices table for BTMC")
            return []

        gold_prices = []
        rows = table.find('tbody').find_all('tr')[1:]

        for row in rows:
            cells = row.find_all('td')
            if cells[0].find('img'):
                gold_prices.append({
                    'type': cells[1].text.strip(),
                    'buy_price': format_price(cells[3].text.strip() if cells[3].text.strip() else "N/A", is_btmc=True),
                    'sell_price': format_price(cells[4].text.strip() if cells[4].text.strip() else "N/A", is_btmc=True)
                })
                break

        return gold_prices

    except requests.RequestException as e:
        print(f"Error fetching BTMC webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing BTMC data: {e}")
        return []


def scrape_gold_prices():
    btmh_url = "https://www.baotinmanhhai.vn"
    btmc_url = "https://btmc.vn"

    results = []

    btmh_prices = scrape_gold_prices_btmh(btmh_url)
    for price in btmh_prices:
        results.append({
            'source': 'Bao Tin Manh Hai',
            'type': price['type'],
            'buy_price': price['buy_price'],
            'sell_price': price['sell_price']
        })

    btmc_prices = scrape_btmc_gold_prices(btmc_url)
    for price in btmc_prices:
        results.append({
            'source': 'Bao Tin Minh Chau',
            'type': price['type'],
            'buy_price': price['buy_price'],
            'sell_price': price['sell_price']
        })

    return results


def check_and_send_updates(context):
    global previous_prices
    prices = scrape_gold_prices()
    
    # Keep track of which sources have updated prices
    any_price_changed = False  # Flag to track if any price changed
    update_messages = []
    
    for item in prices:
        source = item['source']
        current_price = {
            'type': item['type'],
            'buy_price': item['buy_price'],
            'sell_price': item['sell_price']
        }

        # Check if prices have changed
        if previous_prices[source] != current_price:
            any_price_changed = True  # Set flag that at least one price changed
            message = (
                f"📊 *{source} Price Update* 📊\n"
                f"Type: {item['type']}\n"
                f"Buy Price: {item['buy_price']} VND\n"
                f"Sell Price: {item['sell_price']} VND\n"
                f"Website: {source_urls[source]}"
            )
            update_messages.append(message)
            previous_prices[source] = current_price
    
    # Send a single message with all updates if any price changed
    # This guarantees a message is sent if at least one source changed
    if any_price_changed:
        divider = "\n----------------------\n"
        combined_message = divider.join(update_messages)
        combined_message += f"\n\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        context.bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=combined_message,
            parse_mode='Markdown'
        )


def main():
    # Initialize the bot
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    # Schedule price check every minute
    updater.job_queue.run_repeating(check_and_send_updates, interval=INTERVAL, first=1)

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()