import requests
from bs4 import BeautifulSoup
import traceback
from datetime import datetime
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

INTERVAL = int(os.environ.get("INTERVAL", 3600))
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


def check_and_send_updates():
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
                f"Sell Price: {item['sell_price']} VND"
            )
            update_messages.append(message)
            previous_prices[source] = current_price
    
    # Send a single message with all updates if any price changed
    # This guarantees a message is sent if at least one source changed
    if any_price_changed:
        divider = "\n----------------------\n"
        combined_message = divider.join(update_messages)
        combined_message += f"\n\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        combined_message += f"\n________________________________________________________________________"
        
        # Send message to Slack
        send_to_slack(combined_message)
        
        # Send message to Discord
        send_to_discord(combined_message)


def send_to_slack(message):
    """Send a message to Slack using the webhook URL"""
    try:
        # Format message for Slack (Slack uses different markdown syntax)
        # Replace Telegram's *bold* with Slack's *bold*
        # We don't need to modify since both use the same syntax for bold
        
        payload = {'text': message}
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print(f"Message sent to Slack, status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending message to Slack: {e}")


def send_to_discord(message):
    """Send a message to Discord using the webhook URL"""
    try:
        # Discord uses a different payload format than Slack
        payload = {'content': message}
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print(f"Message sent to Discord, status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending message to Discord: {e}")


def main():
    print(f"Starting gold price monitoring service, checking every {INTERVAL} seconds")
    
    while True:
        try:
            check_and_send_updates()
            print(f"Checked prices at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        # Sleep for the interval duration
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()