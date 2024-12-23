# Import libraries
import time
import logging
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt
from app_scraper_logging import fetch_urls_to_crawl, convert_to_jalali, give_information_app, get_or_create_app_id, log_scrape
# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Define the time to run
SCHEDULED_HOUR = 12
SCHEDULED_MINUTE = 52

# Retry decorator for handling transient errors in scraping
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def process_app_info(app_id, app_nickname, app_url, last_base_64, app_scraped_time, app_scraped_time_jalali):
    logging.info(f"Processing app_id {app_id}, nickname: {app_nickname}")
    
    # Scrape app data
    app_data = give_information_app(app_id, app_nickname, app_url, last_base_64)

    if app_data:
        # Update app_info and retrieve the app_id
        app_id = get_or_create_app_id(app_data)

        # Log the scrape
        log_scrape(app_data, app_id, app_nickname, app_scraped_time, app_scraped_time_jalali)
    else:
        logging.warning(f"Failed to scrape app information for app_id {app_id}, nickname: {app_nickname}")


def run_daily_task():
    """Run the daily scheduled task to update app information."""
    while True:
        now = datetime.now()
        logging.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Check if it's the scheduled time
        if now.hour == SCHEDULED_HOUR and now.minute == SCHEDULED_MINUTE:
            logging.info("Scheduled time reached. Starting app info update...")
            try:
                urls_to_crawl = fetch_urls_to_crawl()

                app_time_now = datetime.now()  # Capture the current time when the scraping session starts
                app_scraped_time = datetime.now()
                app_scraped_time_jalali = convert_to_jalali(app_time_now)

                for app_id, app_nickname, app_url, last_base_64 in urls_to_crawl:
                    try:
                        process_app_info(app_id, app_nickname, app_url, last_base_64, app_scraped_time, app_scraped_time_jalali)
                    except Exception as e:
                        logging.error(f"Error processing app_id {app_id}, nickname: {app_nickname}: {e}")

                logging.info("App info update completed successfully.")
            except Exception as e:
                logging.error(f"Error during app info update: {e}")

            # Sleep for a day to avoid running the task multiple times in the same minute
            logging.info("Sleeping until the next scheduled time...")
            time.sleep(82800)
        else:
            # Sleep for 1 minute before checking the time again
            time.sleep(60)


if __name__ == "__main__":
    logging.info("Starting daily app info updater...")
    run_daily_task()
