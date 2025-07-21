# Import libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
from tqdm import tqdm
from datetime import datetime
import random
# To solve timeout problem
from tenacity import retry, wait_exponential, stop_after_attempt
from selenium.common.exceptions import TimeoutException
# Connect to database
from connect_to_database_func import connect_db
# Convert to jalali
from convert_to_jalali_func import convert_to_jalali
from logging_config import setup_logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = setup_logger('comment_scraper', 'comment_scraper.log')

def save_details_to_app_info(app_id, count_scraped_comments, count_new_comments, comment_scraped_time):
    """Update or insert app information into the app_info table."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        check_query = "SELECT COUNT(*) FROM public.app_info WHERE app_id = %s;"
        cursor.execute(check_query, (app_id,))
        fetch_result = cursor.fetchone()
        exists = fetch_result is not None and fetch_result[0] > 0

        if exists:
            update_query = """
            UPDATE public.app_info
            SET count_scraped_comments = %s,
                count_new_comments = %s,
                last_update_comment_scraping = %s
            WHERE app_id = %s;
            """
            cursor.execute(update_query, (count_scraped_comments, count_new_comments, comment_scraped_time, app_id))
            logger.info(f"Updated app_info for app_id {app_id} with {count_scraped_comments} total and {count_new_comments} new comments.")
        else:
            insert_query = """
            INSERT INTO public.app_info (app_id, count_scraped_comments, count_new_comments, last_update_comment_scraping)
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(insert_query, (app_id, count_scraped_comments, count_new_comments, comment_scraped_time))
            logger.info(f"Inserted new record into app_info for app_id {app_id}.")
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating app_info for app_id {app_id}: {e}", exc_info=True)
    finally:
        cursor.close()
        conn.close()


def fetch_app_urls_to_crawl(app_ids=None):
    """Fetch app IDs and URLs to crawl from the app_info table."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        if app_ids:
            query = """SELECT app_id, app_url FROM public.app_info WHERE app_id = ANY(%s) AND active = TRUE AND deleted = FALSE"""
            cursor.execute(query, (app_ids,))
        else:
            query = "SELECT app_id, app_url FROM public.app_info"
            cursor.execute(query)
        apps = cursor.fetchall()
        logger.info(f"Fetched {len(apps)} apps to crawl.")
        return apps
    except Exception as e:
        logger.error(f"Error fetching app URLs to crawl: {e}", exc_info=True)
        return []
    finally:
        cursor.close()
        conn.close()


def save_comments_to_db(comments):
    """Save comments in the database, ensuring uniqueness on `comment_idd`."""
    if not comments:
        logger.warning("No comments to insert.")
        return 0

    conn = connect_db()
    cursor = conn.cursor()
    try:
        insert_query = """
        INSERT INTO public.comment (app_id, user_name, comment_text, comment_rating, comment_date, second_model_processed, comment_idd, comment_date_jalali)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (comment_idd) DO NOTHING;
        """
        cursor.executemany(insert_query, comments)
        new_comments_count = cursor.rowcount
        conn.commit()

        reset_query = """
        SELECT setval(pg_get_serial_sequence('public.comment', 'comment_id'), COALESCE(MAX(comment_id), 1)) FROM public.comment;
        """
        cursor.execute(reset_query)
        conn.commit()
        logger.info(f"Inserted {new_comments_count} new comments into the database.")
        return new_comments_count
    except Exception as e:
        logger.error("Error inserting comments into the database.", exc_info=True)
        return 0
    finally:
        cursor.close()
        conn.close()


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def load_page(driver, url):
    """Load a page with retries."""
    try:
        driver.get(url)
        logger.info(f"Successfully loaded page: {url}")
    except Exception as e:
        logger.error(f"Error loading page {url}: {e}", exc_info=True)
        raise


def crawl_comments(app_id, app_url):
    """Crawl comments for a specific app."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")

    chrome_service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    # Set a longer page load timeout
    driver.set_page_load_timeout(350)

    try:
        load_page(driver, app_url.split('?l=')[0] + '?l=en')
    except TimeoutException:
        logger.error(f"Timeout while loading page for app_id {app_id}.")
        driver.quit()
        return

    wait = WebDriverWait(driver, 10)
    
    # Scroll down to load initial comments
    total_clicks = 0
    while True:
        click_count = 0
        while click_count < 126:
            try:
                time.sleep(random.uniform(2, 5))
                load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'AppCommentsList__loadmore')))
                driver.execute_script("arguments[0].click();", load_more_button)
                click_count += 1
                total_clicks += 1
                print(f"Clicked 'Load more' {total_clicks} times.")
                time.sleep(10)
            except Exception:
                print("No more 'Load more' button found, or end of comments reached.")
                break

        print("Simulating session refresh...")
        driver.delete_all_cookies()
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        if click_count < 126:
            break

    logger.info(f"Scraping comments for app_id {app_id}.")
    comments_elements = driver.find_elements(By.CLASS_NAME, 'AppComment')
    logger.info(f"Found {len(comments_elements)} comments for app_id {app_id}.")

    count_scraped_comments = len(comments_elements)
    scraped_time_now = datetime.now().strftime("%Y-%m-%d")
    comment_scraped_time = convert_to_jalali(scraped_time_now)

    comments_data = []
    for comment in tqdm(comments_elements, desc="Processing comments"):
        try:
            username = comment.find_element(By.CLASS_NAME, 'AppComment__username').text
            comment_text = comment.find_element(By.CLASS_NAME, 'AppComment__body').text
            date = comment.find_element(By.CLASS_NAME, 'AppComment__meta').text
            comment_id_str = comment.get_attribute('id')
            if comment_id_str is not None:
                comment_idd = int(comment_id_str)
            else:
                logger.warning("Comment element missing 'id' attribute; skipping this comment.")
                continue
            style_attr = comment.find_element(By.CLASS_NAME, 'rating__fill').get_attribute('style')
            if style_attr is not None:
                try:
                    rating_percent = style_attr.split()[1].split('%')[0]
                    rating = int(rating_percent) / 20
                except (IndexError, ValueError):
                    logger.warning(f"Unexpected style format for rating: '{style_attr}'. Setting rating to 0.")
                    rating = 0
            else:
                logger.warning("No 'style' attribute found for rating. Setting rating to 0.")
                rating = 0
            try:
                converted_date = datetime.strptime(date, "%Y/%m/%d").strftime("%Y-%m-%d")
                comment_date_jalali = convert_to_jalali(converted_date)
            except ValueError:
                converted_date = datetime.now().strftime("%Y-%m-%d")
                comment_date_jalali = convert_to_jalali(converted_date)

            comments_data.append((app_id, username, comment_text, rating, converted_date, False, comment_idd, comment_date_jalali))
        except Exception as e:
            logger.error(f"Error processing comment for app_id {app_id}: {e}", exc_info=True)

    new_comments_count = save_comments_to_db(comments_data)
    save_details_to_app_info(app_id, count_scraped_comments, new_comments_count, comment_scraped_time)
    driver.quit()
