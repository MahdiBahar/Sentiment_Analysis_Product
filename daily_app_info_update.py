## In this code we use app_scrapping function to execute daily

# Import libraries
import time
import logging
from datetime import datetime
from app_scraper_logging import fetch_urls_to_crawl, convert_to_jalali, give_information_app, get_or_create_app_id, log_scrape
# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Define the time to run the script (24-hour format)
SCHEDULED_HOUR = 7  
SCHEDULED_MINUTE = 41

def run_daily_task():

    while True:
        now = datetime.now()
        logging.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if it's the scheduled time
        if now.hour == SCHEDULED_HOUR and now.minute == SCHEDULED_MINUTE:
            logging.info("Scheduled time reached. Starting app info update...")
            try:
                # crawl_and_update_app_info()  # Call your function here
                urls_to_crawl = fetch_urls_to_crawl() 

                app_time_now = datetime.now() 
                app_scraped_time = datetime.now() 
                app_scraped_time_jalali = convert_to_jalali(app_time_now)
 
                for crawl_app_name, crawl_url in urls_to_crawl:
                    print(f"Scraping {crawl_app_name} at {crawl_url}")
                    app_data = give_information_app(crawl_app_name, crawl_url)

                    if app_data:
                        # Update app_info and retrieve the app_id
                        app_id = get_or_create_app_id(app_data)

                        # Log the scrape with the explicit scraped_time
                        log_scrape(app_data, app_id, app_scraped_time, app_scraped_time_jalali)
                logging.info("App info update completed successfully.")
            except Exception as e:
                logging.error(f"Error during app info update: {e}")
            
            # Sleep for a day to avoid running the task multiple times in the same minute
            time.sleep(82800)
        else:
            # Sleep for 1 minute before checking the time again
            time.sleep(60)

if __name__ == "__main__":
    logging.info("Starting daily app info updater...")
    run_daily_task()