# Import libraries
import time
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt
from app_scraper_logging import fetch_urls_to_crawl, give_information_app, get_or_create_app_id, log_scrape
from convert_to_jalali_func import convert_to_jalali
from logging_config import setup_logger

# Setup logger
logger = setup_logger('daily_task', 'daily_task.log')

# Define the time to run
SCHEDULED_HOUR = 10
SCHEDULED_MINUTE = 31

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def process_app_info(app_id, app_nickname, app_url, last_base_64, app_scraped_time, app_scraped_time_jalali):
    """
    Process app information by scraping and logging results.
    """
    logger.info(f"Processing app_id {app_id}, nickname: {app_nickname}")

    # Scrape app data
    try:
        app_data = give_information_app(app_id, app_nickname, app_url, last_base_64)

        if app_data:
            # Update app_info and retrieve the app_id
            app_id = get_or_create_app_id(app_data , app_nickname)
            logger.info(f"Updated app_info for app_id {app_id}, nickname: {app_nickname}")

            # Log the scrape
            log_scrape(app_data, app_id, app_nickname, app_scraped_time, app_scraped_time_jalali)
            logger.info(f"Logged scrape for app_id {app_id}, nickname: {app_nickname}")
        else:
            logger.warning(f"Failed to scrape app information for app_id {app_id}, nickname: {app_nickname}")
    except Exception as e:
        logger.error(f"Error in process_app_info for app_id {app_id}, nickname: {app_nickname}: {e}", exc_info=True)


def run_daily_task():
    """Run the daily scheduled task to update app information."""
    while True:
        now = datetime.now()
        logger.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Check if it's the scheduled time
        if now.hour == SCHEDULED_HOUR and now.minute == SCHEDULED_MINUTE:
            logger.info("Scheduled time reached. Starting app info update...")
            try:
                urls_to_crawl = fetch_urls_to_crawl()
                logger.info(f"Fetched {len(urls_to_crawl)} URLs to crawl.")

                app_time_now = datetime.now()
                app_scraped_time = app_time_now
                app_scraped_time_jalali = convert_to_jalali(app_time_now)

                for app_id, app_nickname, app_url, last_base_64 in urls_to_crawl:
                    try:
                        process_app_info(app_id, app_nickname, app_url, last_base_64, app_scraped_time, app_scraped_time_jalali)
                    except Exception as e:
                        logger.error(f"Error processing app_id {app_id}, nickname: {app_nickname}: {e}", exc_info=True)

                logger.info("App info update completed successfully.")
            except Exception as e:
                logger.error(f"Error during app info update: {e}", exc_info=True)

            # Sleep for a day to avoid running the task multiple times in the same minute
            logger.info("Sleeping until the next scheduled time...")
            time.sleep(82800)
        else:
            # Sleep for 1 minute before checking the time again
            time.sleep(60)


if __name__ == "__main__":
    logger.info("Starting daily app info updater...")
    run_daily_task()
