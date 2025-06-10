import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from datetime import datetime
import re
import sys
import os 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('price_tracker.log'), logging.StreamHandler()]
)

# Configuration
CONFIG_FILE = 'price_config.json'
PRODUCT_NAME = "Sony Xperia 1 VI"

# URLs to check (in order of priority)
URLS = [
    "https://store.sony.com.sg/products/xperia-1m6/?locale=en",  # Sony Store
    # "https://www.sony.com.sg/smartphones/products/xperia-1m6",   # Sony Product Page
    # URL = "https://www.sony.com.sg/electronics/smartphones/xperia-1m6"  # Sony Singapore URL for Xperia 1 VI
    # URL = "https://store.sony.com.sg/products/xperia-1m6/?locale=en&variant=44772202250395"  # Sony Singapore URL for Xperia 1 VI
    # "https://store.sony.com.sg/products/xperia-1m6/"  # Sony Singapore URL for Xperia 1 VI
]

CHECK_INTERVAL = 6 * 60 * 60  # Check every 6 hours by default

# Default configuration
DEFAULT_CONFIG = {
    "email": {
        "sender_email": "your_email@example.com",
        "sender_name": "Price Tracker",
        "api_key": "your_brevo_api_key",  # Replace with your Brevo API key
        "recipient_email": "recipient@example.com"
    },
    "price": {
        "last_price": None,
        "last_checked": None,
        "original_price": 1989.0  # Store the original non-discounted price
    },
    "check_interval": CHECK_INTERVAL
}

def load_config():
    """Load configuration from file or create default if it doesn't exist"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        logging.info(f"Created default configuration file: {CONFIG_FILE}")
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def extract_price(text):
    """Extract a price from text - handles $ sign format"""
    # First try to match a standard price format with $ sign
    price_pattern = r'\$([\d,]+\.?\d*)'
    match = re.search(price_pattern, text)
    if match:
        try:
            # Remove commas and convert to float
            price_str = match.group(1).replace(',', '')
            return float(price_str)
        except (ValueError, AttributeError):
            return None
    return None

def save_debug_html(url, html_content):
    """Save HTML content for debugging"""
    try:
        debug_file = f"debug_{url.split('/')[-1]}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"Saved debug HTML to {debug_file}")
    except Exception as e:
        logging.error(f"Failed to save debug HTML: {e}")

def get_price():
    """Try to scrape price from multiple URLs and using different methods"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # This will store all valid prices we find
    valid_prices = []
    
    # Try each URL in order
    for url in URLS:
        logging.info(f"Trying to fetch price from: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try common price selectors
            price_selectors = ['.product__price', '.price', '.product-price']
            
            logging.info("Looking for price elements...")
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.text.strip()
                    logging.info(f"Found element with selector '{selector}': {price_text}")
                    
                    price = extract_price(price_text)
                    if price:
                        logging.info(f"Successfully extracted price: ${price}")
                        if 500 < price < 3000:  # Reasonable price range for a smartphone
                            logging.info(f"Price is in valid range: ${price}")
                            valid_prices.append(price)
                        else:
                            logging.warning(f"Price ${price} outside expected range (500-3000)")
            
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
    
    # If we found at least one valid price, return the lowest one
    if valid_prices:
        lowest_price = min(valid_prices)
        logging.info(f"Using lowest valid price found: ${lowest_price}")
        return lowest_price
    
    # No valid price found
    logging.error("Failed to find a valid price")
    return None

def send_email(config, current_price, previous_price):
    """Send email notification using Brevo API"""
    sender_email = config['email']['sender_email']
    sender_name = config['email']['sender_name']
    api_key = config['email']['api_key']
    recipient_email = config['email']['recipient_email']
    
    if api_key == 'your_brevo_api_key':
        logging.warning("Brevo API key not set. Please update the config file.")
        return False
    
    # Get original price (if available)
    original_price = config['price'].get('original_price', 1989.0)
    
    # Calculate price differences
    price_diff = previous_price - current_price
    percentage_drop = (price_diff / previous_price) * 100
    
    # Calculate discount from original price
    discount_amount = original_price - current_price
    discount_percentage = (discount_amount / original_price) * 100
    
    # Create email content
    subject = f"Price Drop Alert: {PRODUCT_NAME}"
    content = f"""Good news! The price of {PRODUCT_NAME} has dropped.

Previous price: ${previous_price:.2f}
Current price: ${current_price:.2f}
You save: ${price_diff:.2f} ({percentage_drop:.1f}% drop)

Original price: ${original_price:.2f}
Current discount: ${discount_amount:.2f} ({discount_percentage:.1f}% off)

Check it out at: {URLS[0]}

This notification was sent by your Price Tracker script.
"""
    
    try:
        # Using requests to call Brevo API
        url = "https://api.brevo.com/v3/smtp/email"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": api_key
        }
        
        data = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": recipient_email
                }
            ],
            "subject": subject,
            "htmlContent": content.replace("\n", "<br>")
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201, 202]:
            logging.info("Price drop email notification sent successfully")
            return True
        else:
            logging.error(f"Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def check_price_and_notify():
    """Main function to check price and send notification if needed"""
    config = load_config()
    current_price = get_price()
    
    if current_price is None:
        logging.warning("Could not retrieve current price. Skipping this check.")
        return
    
    last_price = config['price']['last_price']
    
    # Update last checked time
    config['price']['last_checked'] = datetime.now().isoformat()
    
    if last_price is None:
        # First time checking, just save the price
        config['price']['last_price'] = current_price
        logging.info(f"Initial price recorded: S${current_price}")
    elif current_price < last_price:
        # Price has dropped, send notification
        logging.info(f"Price drop detected! From S${last_price} to S${current_price}")
        send_email(config, current_price, last_price)
        # Update the last price
        config['price']['last_price'] = current_price
    elif current_price > last_price:
        # Price has increased
        logging.info(f"Price increased from S${last_price} to S${current_price}")
        config['price']['last_price'] = current_price
    else:
        # Price unchanged
        logging.info(f"Price unchanged: S${current_price}")
    
    # Save updated config
    save_config(config)

def run_once_direct():
    """Run the price check once and update config directly"""
    logging.info(f"{PRODUCT_NAME} Price Check - Direct Run Mode")
    
    # Load config
    config = load_config()
    
    # Get price directly
    current_price = get_price()
    logging.info(f"Direct price result: {current_price}")
    
    if current_price is not None:
        last_price = config['price']['last_price']
        
        # Update last checked timestamp
        config['price']['last_checked'] = datetime.now().isoformat()
        
        if last_price is None:
            # First time checking, just save the price
            config['price']['last_price'] = current_price
            logging.info(f"Initial price recorded: ${current_price}")
        elif current_price < last_price:
            # Price has dropped, send notification
            logging.info(f"Price drop detected! From ${last_price} to ${current_price}")
            send_email(config, current_price, last_price)
            # Update the last price
            config['price']['last_price'] = current_price
        elif current_price > last_price:
            # Price has increased
            logging.info(f"Price increased from ${last_price} to ${current_price}")
            config['price']['last_price'] = current_price
        else:
            # Price unchanged
            logging.info(f"Price unchanged: ${current_price}")
        
        # Save config
        save_config(config)
        logging.info(f"Config updated with price: ${current_price}")
    else:
        logging.warning("Could not retrieve price. Config not updated.")
    
    logging.info("Direct price check complete")

def main():
    """Main function to run the price tracker"""
    logging.info(f"{PRODUCT_NAME} Price Tracker started")
    
    # Load configuration
    config = load_config()
    
    # Check if email configuration is set
    if config['email']['api_key'] == 'your_brevo_api_key':
        logging.warning("Brevo API key not configured. Please update the config file.")
    
    try:
        # Run the initial check
        check_price_and_notify()
        
        # Continue checking at intervals
        check_interval = config.get('check_interval', CHECK_INTERVAL)
        
        logging.info(f"Price tracker will check every {check_interval/3600:.1f} hours")
        
        while True:
            time.sleep(check_interval)
            check_price_and_notify()
                
    except KeyboardInterrupt:
        logging.info("Price tracker stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        run_once_direct()  # Use the direct version
    else:
        main()
