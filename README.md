im using github here for the first time, not sure what to do - hopefully the instructions make sense 

# Price Tracker

## Purpose
Automatically monitors a product's price on a website and sends email notifications when the price drops.

## Setup Instructions

1. **Install required libraries**: pip install requests==2.31.0 beautifulsoup4==4.12.2


2. **Configure the tracker**:
   - Place both `price_tracker.py` and [price_config.json] in the same directory
   - Edit [price_config.json] with your details:
     ```json
     {
       "email": {
         "sender_email": "your_email@example.com",
         "sender_name": "Your Preferred Name",
         "api_key": "your_brevo_api_key",
         "recipient_email": "email_to_receive_alerts@example.com"
       }
     }
     ```
   - [Create a free Brevo account](https://www.brevo.com/free/) to get your API key
   - Optionally adjust `last_price` to set your starting price point
   - Optionally change `check_interval` (in seconds) - default is 6 hours

3. **Customize product**:
   - In `price_tracker.py`, edit the URLs list to monitor your desired product

4. **Run the tracker**:
   - For a one-time check: `python price_tracker.py --once`
   - For continuous monitoring: `python price_tracker.py`

## Features
- Tracks price changes over time
- Sends email notifications only when price drops
- Compares current price to both previous price and original price
- Configurable check intervals
