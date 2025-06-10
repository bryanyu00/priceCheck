im using github here for the first time, not sure what to do - hopefully the instructions make sense 

purpose: to check a product page's website, see its prices, then sends an email to alert me when the price drops. 

but i believe if you want to run the code, you can download it, put both files in the same directory:
1) edit the json file with your sender_email, sender_name, api_key, receipient_email [i'm using the email service called Brevo - as it works for me here to send an email through that service]
2) if you want, you can edit the "last_price" in the json file to an amount you want to start with
3) if you want, you can change the "check_interval" in the json file too, to an interval you prefer, now it's 6 hours

4) in the main py file, you could edit the product link of which you want to price watch from

5) what works for me is in the cmd terminal, with all the necessary library installed, i just ran: python3 price_tracker.py --once


remember to install these necessary libraries:
1) requests==2.31.0
2) beautifulsoup4==4.12.2
