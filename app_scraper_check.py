# Import libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
#convert to base64
from convert_image_to_base64_func import convert_image_to_base64
# to solve time out problem
from tenacity import retry, wait_exponential, stop_after_attempt
from selenium.common.exceptions import TimeoutException
#for Extracting package name
from urllib.parse import urlparse
# Connect to database
from connect_to_database_func import connect_db
from dotenv import load_dotenv
from convert_image_to_base64_func import convert_image_to_base64
from logging_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = setup_logger('app_scraper_check', 'app_scraper_check.log')


def extract_app_package_name(url):
    """Extract the app package name from a given URL."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if hostname == "cafebazaar.ir":
            path = parsed_url.path.rstrip("/")
            package_name = path.split("/")[-1]
            logger.info(f"Extracted package name: {package_name}")
            return package_name, None
        logger.error(f"Invalid hostname: {hostname}")
        return None, "host-error"
    except Exception as e:
        logger.error(f"Error extracting package name: {e}", exc_info=True)
        return None, "url-error"


def check_and_create_app_id(data):
    """Check if an app exists and update or create its record."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if app already exists in app_info
        select_query = "SELECT app_id, deleted FROM app_info WHERE app_name = %s AND app_nickname = %s;"
        cursor.execute(select_query, (data['App_Name'], data['App_Nickname']))
        result = cursor.fetchone()

        if result[0]:
            
            if result[1]:
                app_id = result[0]  # Assuming result[0] contains the correct app_id

                update_query = """
                    UPDATE app_info
                    SET 
                        app_name = %s, 
                        app_img = %s, 
                        app_name_company = %s, 
                        app_version = %s, 
                        app_total_rate = %s, 
                        app_average_rate = %s, 
                        app_install = %s, 
                        app_category = %s, 
                        app_size = %s, 
                        app_last_update = %s, 
                        app_url = %s, 
                        app_img_base64 = %s, 
                        app_nickname = %s, 
                        deleted = %s
                    WHERE app_id = %s;
                """
                cursor.execute(update_query, (
                    data['App_Name'], data['App_Img'], data['App_Name_Company'], data['App_Version'],
                    data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'], data['App_Category'],
                    data['App_Size'], data['App_Last_Update'], data['App_URL'], data['App_Img_Base64'],
                    data['App_Nickname'], False, app_id
                ))
                conn.commit()
                long_report = 'Deleted app reactivated'
                short_report = 'deleted-back'
                logger.info(f"Reactivated deleted app with app_id: {app_id}")
                # return "Deleted app reactivated"
            else:
                long_report = f'Duplicate app. {data['App_Nickname']} with {data['App_URL']} exists. Try again to add another application'
                short_report = "Duplicate"
                logger.warning(f"Duplicate app detected: {data['App_Name']} ({data['App_URL']})")
                # return "Duplicate app"
        else:
            if data['App_Category'] in ["امور مالی", "شبکه‌های اجتماعی"]:
                # Reset the sequence after insert to ensure sequential IDs
                reset_query = """
                SELECT setval(pg_get_serial_sequence('app_info', 'app_id'), COALESCE(MAX(app_id), 1)) FROM app_info;
                """
                cursor.execute(reset_query)
                conn.commit()

                # App doesn't exist, insert it into app_info
                insert_query = """
                INSERT INTO app_info (
                    app_name, app_img, app_name_company, app_version, app_total_rate, 
                    app_average_rate, app_install, app_category, app_size, app_last_update, 
                    app_url, app_img_base64, app_nickname
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING app_id;
                """
                cursor.execute(insert_query, (
                    data['App_Name'], data['App_Img'], data['App_Name_Company'], data['App_Version'],
                    data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
                    data['App_Category'], data['App_Size'], data['App_Last_Update'], 
                    data['App_URL'], data['App_Img_Base64'], data['App_Nickname']
                ))

                app_id = cursor.fetchone()[0]  # Retrieve the new app_id after insertion
                long_report = 'New URL is added'
                short_report = 'Valid'
                conn.commit()
                logger.info(f"Added new app with app_id: {app_id}")
                # return "New app added"
            else:
                long_report = 'URL is valid but this application is not related to Financial Applications'
                short_report = 'Irrelevant'
                logger.warning(f"Irrelevant app category: {data['App_Category']} for {data['App_Name']}")
                # return "Irrelevant app category"
        cursor.close()
        conn.close()
    except Exception as e:
        long_report = f'Something happened. Check the connection or validity of URL: {data['App_URL']}'
        short_report = 'Connection-Error'
        logger.warning(f"message : {long_report}")
        logger.error(f"Error in check_and_create_app_id: {e}", exc_info=True)
        
        # return "Error occurred"
    return [long_report, short_report]



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


def give_information_app(app_nickname, url):
    """Scrape app information from the given URL."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(options=chrome_options)
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
            continue

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

        App_Img_Base64 = convert_image_to_base64(App_Img)
        app_package_name = extract_app_package_name(url)

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
            'App_Img_Base64': App_Img_Base64,
            'App_Nickname': app_package_name[0]
        }
        # logger.info(f"Scraped data: {APP_INFO}")
    except Exception as e:
        logger.error(f"Error extracting app details: {e}", exc_info=True)
        APP_INFO = None

    driver.quit()
    return APP_INFO
