# Import libraries
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import hashlib
from tqdm import tqdm
from datetime import datetime
import os
import random
# to solve time out problem
from tenacity import retry, wait_exponential, stop_after_attempt
from selenium.common.exceptions import TimeoutException


# Database connection function
def connect_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "MEC-Sentiment"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )
    return conn


# Fetch app_ids and app_urls from the app_info table
def fetch_app_urls_to_crawl():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT app_id, app_url FROM public.app_info")
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return apps


 #Function to save comments in batches with uniqueness enforced on `comment_idd`
def save_comments_to_db(comments):
    if not comments:
        return
    conn = connect_db()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO public.comment (app_id, user_name, comment_text, comment_rating, comment_date, sentiment_processed, iid, comment_idd)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (comment_idd) DO NOTHING;
    """
    cursor.executemany(insert_query, comments)
    conn.commit()
        # Reset the sequence after insert to ensure sequential IDs
    reset_query = """
    SELECT setval(pg_get_serial_sequence('public.comment', 'comment_id'), COALESCE(MAX(comment_id), 1)) FROM public.comment;
    """
    cursor.execute(reset_query)
    conn.commit()
    
    cursor.close()
    conn.close()


# Retry with exponential backoff for driver.get
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def load_page(driver, url):
    driver.get(url)

def crawl_comments(app_id, app_url):
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
        print(f"Failed to load the page for app ID {app_id} after retries.")
        driver.quit()
        return
    
    wait = WebDriverWait(driver, 10)
    
    # Scroll down to load initial comments
    total_clicks = 0
    while True:
        # Restart logic without reloading the URL
        click_count = 0
        while click_count < 126:
            try:
                # Random delay to avoid detection
                time.sleep(random.uniform(2, 5))
                load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'AppCommentsList__loadmore')))
                driver.execute_script("arguments[0].click();", load_more_button)
                click_count += 1
                total_clicks += 1
                print(f"Clicked 'Load more' {total_clicks} times.")
                time.sleep(10)  # Allow time for comments to load
            except Exception:
                print("No more 'Load more' button found, or end of comments reached.")
                break
        
        # Clear cookies to simulate a new session, but continue from current scroll
        print("Simulating session refresh...")
        driver.delete_all_cookies()  # Clear cookies to "refresh" the session
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to where we left off

        # Re-attempt "Load more" after session reset
        if click_count < 126:  # If click_count is less than the click numbers in this cycle, we assume we're done
            break

    # Extract comments after all clicks are complete
    print(f"Scraping comments for app ID {app_id}...")
    comments_elements = driver.find_elements(By.CLASS_NAME, 'AppComment')
    print(f"Found {len(comments_elements)} comments for app ID {app_id}.")

    comments_data = []
    for comment in tqdm(comments_elements):
        try:
            username = comment.find_element(By.CLASS_NAME, 'AppComment__username').text
            comment_text = comment.find_element(By.CLASS_NAME, 'AppComment__body').text
            date = comment.find_element(By.CLASS_NAME, 'AppComment__meta').text

            try:
                # Get the `id` attribute and directly convert it to an integer
                comment_idd = int(comment.get_attribute('id'))
               
            except ValueError as e:
                print(f"Failed to convert comment ID to integer: {e}")
            except Exception as e:
                print(f"Error extracting comment ID: {e}")

            # Extract rating if available
            try:
                rating = int(comment.find_element(By.CLASS_NAME, 'rating__fill').get_attribute('style').split()[1].split('%')[0]) / 20
            except:
                rating = None

            # Generate unique `iid`
            iid = hashlib.sha256((username + comment_text + date).encode('utf-8')).hexdigest()

            # Convert date to standard format
            try:
                converted_date = datetime.strptime(date, "%Y/%m/%d").strftime("%Y-%m-%d")
            except ValueError:
                converted_date = datetime.now().strftime("%Y-%m-%d")

            # Append data to batch list
            comments_data.append((app_id, username, comment_text, rating, converted_date,  False, iid, comment_idd))

        except Exception as e:
            print(f"Error processing a comment for app ID {app_id}: {e}")

    # Save comments in batch
    save_comments_to_db(comments_data)
    driver.quit()


# Main function for crawling comments
def main():
    apps = fetch_app_urls_to_crawl()
    for app_id, app_url in apps:
        print(f"Crawling comments for app at {app_url}")
        if (app_id == 28):  # Start from a specific app ID if needed
            crawl_comments(app_id, app_url)

if __name__ == "__main__":
    main()
