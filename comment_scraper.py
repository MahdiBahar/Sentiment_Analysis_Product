# Import libraries
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import hashlib
from tqdm import tqdm
from datetime import datetime
import os

# Database connection function
def connect_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "MEC_Sentiment"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )
    return conn

# Function to get app_ids and app_urls from the app_info table
def fetch_app_urls_to_crawl():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT app_id, app_url FROM public.app_info")
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return apps

# Function to save comments to the comments table with uniqueness check using iid
def save_comment_to_db(app_id, username, image_url, comment_text, rating, converted_date, iid):
    conn = connect_db()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO public.comment (app_id, user_name, user_image, comment_text, comment_rating, comment_date, iid, sentiment_processed)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (iid) DO NOTHING;  -- Ensures uniqueness using `iid`
    """
    cursor.execute(insert_query, (
        app_id, username, image_url, comment_text, rating, converted_date, iid, False
    ))
    conn.commit()
    cursor.close()
    conn.close()

# Function to crawl and extract comments
def crawl_comments(app_id, app_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(app_url)
    wait = WebDriverWait(driver, 10)

    try:
        # Click the 'Load more' button until comments are fully loaded or a set number of times
        click_count = 0
        click_limit = 10  # Adjust this limit as needed
        while click_count < click_limit:
            try:
                load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'AppCommentsList__loadmore')))
                driver.execute_script("arguments[0].click();", load_more_button)
                click_count += 1
                print(f"Clicked 'Load more' {click_count} times.")
                time.sleep(6)  # Adjust this as needed for page load time
            except Exception as e:
                print(f"No more 'Load more' button found or error: {e}")
                break

        print(f"Scraping comments for app ID {app_id}...")

        # Find all comment elements
        comments = driver.find_elements(By.CLASS_NAME, 'AppComment')
        print(f"Found {len(comments)} comments for app ID {app_id}.")

        for comment in tqdm(comments):
            try:
                username = comment.find_element(By.CLASS_NAME, 'AppComment__username').text
                comment_text = comment.find_element(By.CLASS_NAME, 'AppComment__body').text
                date = comment.find_element(By.CLASS_NAME, 'AppComment__meta').text
                image_url = comment.find_element(By.TAG_NAME, 'img').get_attribute('src')

                # Extract rating if available
                try:
                    rating = int(comment.find_element(By.CLASS_NAME, 'rating__fill').get_attribute('style').split()[1].split('%')[0]) / 20
                except:
                    rating = None

                # Generate unique `iid`
                iid = hashlib.sha256((username + comment_text + date).encode('utf-8')).hexdigest()

                # Convert date to standard format (handle Jalali if needed)
                try:
                    converted_date = datetime.strptime(date, "%Y/%m/%d").strftime("%Y-%m-%d")
                except ValueError:
                    converted_date = datetime.now().strftime("%Y-%m-%d")

                # Save comment to database
                save_comment_to_db(app_id, username, image_url, comment_text, rating, converted_date, iid)

            except Exception as e:
                print(f"Error processing a comment: {e}")

    except Exception as e:
        print(f"Error while loading comments for {app_url}: {e}")

    driver.quit()

# Main function for crawling comments
def main():
    apps = fetch_app_urls_to_crawl()
    for app_id, app_url in apps:
        print(f"Crawling comments for app at {app_url}")
        crawl_comments(app_id, app_url)

if __name__ == "__main__":
    main()
