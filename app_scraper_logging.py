# Import libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
# To solve time out problem
from tenacity import retry, wait_exponential, stop_after_attempt
from selenium.common.exceptions import TimeoutException
# Convert to base64
from convert_image_to_base64_func import convert_image_to_base64
# Connect to database
from connect_to_database_func import connect_db
from dotenv import load_dotenv
from logging_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = setup_logger('app_scraper_logging', 'app_scraper_logging.log')

def fetch_urls_to_crawl():
    """Fetch app URLs to crawl from the app_info table."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        query = """SELECT app_id, app_nickname, app_url, app_img_base64 FROM public.app_info WHERE deleted = FALSE"""
        cursor.execute(query)
        urls = cursor.fetchall()
        logger.info(f"Fetched {len(urls)} URLs to crawl.")
        return urls
    except Exception as e:
        logger.error(f"Error fetching URLs to crawl: {e}", exc_info=True)
        return []
    finally:
        cursor.close()
        conn.close()


def get_or_create_app_id(data):
    """Update or create app entry in app_info."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        select_query = "SELECT app_id FROM app_info WHERE app_name = %s;"
        cursor.execute(select_query, (data['App_Name'],))
        result = cursor.fetchone()

        if result:
            app_id = result[0]
            update_query = """
            UPDATE app_info
            SET app_img = %s, app_name_company = %s, app_version = %s, 
                app_total_rate = %s, app_average_rate = %s, app_install = %s, 
                app_category = %s, app_size = %s, app_last_update = %s, 
                app_img_base64 = %s
            WHERE app_id = %s;
            """
            cursor.execute(update_query, (
                data['App_Img'], data['App_Name_Company'], data['App_Version'],
                data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
                data['App_Category'], data['App_Size'], data['App_Last_Update'],
                data['App_Img_Base64'], app_id
            ))
            logger.info(f"Successfully updated app_info for app_id {app_id}.")
        else:
            logger.error(f"App does not exist in the database for {data['App_Name']}.")
        conn.commit()
        return app_id
    except Exception as e:
        logger.error(f"Error in get_or_create_app_id: {e}", exc_info=True)
        return None
    finally:
        cursor.close()
        conn.close()


def log_scrape(data, app_id, app_nickname, app_scraped_time, app_scraped_time_jalali):
    """Log each scrape into the log_app table."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        log_query = """
        INSERT INTO log_app (
            app_id, app_name, app_name_company, app_version, app_total_rate, 
            app_average_rate, app_install, app_category, app_size, 
            app_last_update, app_scraped_time, app_scraped_time_jalali, app_nickname
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(log_query, (
            app_id, data['App_Name'], data['App_Name_Company'], data['App_Version'],
            data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
            data['App_Category'], data['App_Size'], data['App_Last_Update'],
            app_scraped_time, app_scraped_time_jalali, app_nickname
        ))
        conn.commit()
        logger.info(f"Logged scrape for app_id {app_id}.")
    except Exception as e:
        logger.error(f"Error logging scrape for app_id {app_id}: {e}", exc_info=True)
    finally:
        cursor.close()
        conn.close()


# Function to check if text contains Persian characters
def is_persian(text):
    """Checks if the text contains Persian characters."""
    return any("\u0600" <= char <= "\u06FF" for char in text)

# Retry with exponential backoff for driver.get
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def load_page(driver, url):
    """Load a webpage with retries."""
    try:
        driver.get(url)
        logger.info(f"Page loaded successfully: {url}")
    except Exception as e:
        logger.error(f"Error loading page: {url}: {e}", exc_info=True)
        raise


def give_information_app(app_id, app_name, url, last_base_64):
    """Scrape app information from the given URL."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(options=chrome_options)
    # Set a longer page load timeout
    driver.set_page_load_timeout(350)

    retry_count = 0
    max_retries = 5  # Set a limit to retries

    while retry_count < max_retries:
        try:
            load_page(driver, url)
            wait = WebDriverWait(driver, 20)
            
            # Wait for the main app details
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'AppDetails__col')))
            App_info_zone = driver.find_element(By.CLASS_NAME, 'AppDetails__col')
            App_Name = App_info_zone.find_element(By.CLASS_NAME, 'AppName').text

            if is_persian(App_Name):
                logger.info("App information loaded in Persian.")
                break
            else:
                logger.warning("App information in English. Retrying...")
                retry_count += 1
                time.sleep(2)
                driver.refresh()
        except Exception as e:
            logger.error(f"Error during scraping attempt: {e}", exc_info=True)
            retry_count += 1

    if retry_count == max_retries:
        logger.error(f"Failed to scrape app details after {max_retries} retries.")
        driver.quit()
        return None

    try:
        App_Name_Company = App_info_zone.find_element(By.CLASS_NAME, 'DetailsPageHeader__company').text
        App_Version = App_info_zone.find_element(By.CLASS_NAME, 'DetailsPageHeader__subtitles').text
        App_Install = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[0].text
        App_Total_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__title')[1].text
        App_Average_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[1].text
        App_Category = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[2].text
        App_Size = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[3].text
        App_Last_Update = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[4].text
        App_Img = App_info_zone.find_element(By.TAG_NAME, 'img').get_attribute('src')

        App_Img_Base64 = convert_image_to_base64(App_Img, last_base_64)
        APP_INFO = {
            'App_Name': App_Name,
            'App_Img': App_Img,
            'App_Name_Company': App_Name_Company,
            'App_Version': App_Version,
            'App_Total_Rate': App_Total_Rate,
            'App_Average_Rate': App_Average_Rate,
            'App_Install': App_Install,
            'App_Category': App_Category,
            'App_Size': App_Size,
            'App_Last_Update': App_Last_Update,
            'App_URL': url,
            'App_Img_Base64': App_Img_Base64
        }
        # logger.info(f"Scraped data: {APP_INFO}")
    except Exception as e:
        logger.error(f"Error extracting app details for app_id {app_id}: {e}", exc_info=True)
        APP_INFO = None

    driver.quit()
    return APP_INFO
