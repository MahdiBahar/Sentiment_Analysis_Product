# Import libraries
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import os
import base64
import requests
from io import BytesIO
# to solve time out problem
from tenacity import retry, wait_exponential, stop_after_attempt
from selenium.common.exceptions import TimeoutException


# Function to download an image and convert it to a base64 string
def convert_image_to_base64(image_url):
    try:
        response = requests.get(image_url)
        # Check if the request was successful
        response.raise_for_status()  
        # Read image data as bytes
        img_data = BytesIO(response.content)  
        # Encode to base64 and decode to string
        base64_img = base64.b64encode(img_data.getvalue()).decode('utf-8')  
        return base64_img
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return None


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

# Function to get URLs from the `urls_to_crawl` table
def fetch_urls_to_crawl():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT crawl_app_name, crawl_url FROM public.url_to_crawl")
    urls = cursor.fetchall()
    cursor.close()
    conn.close()
    return urls


def get_or_create_app_id(data):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if app already exists in app_info
    select_query = "SELECT app_id FROM app_info WHERE app_name = %s;"
    cursor.execute(select_query, (data['App_Name'],))
    result = cursor.fetchone()

    if result:
        # App exists, update the details in app_info
        app_id = result[0]
        update_query = """
        UPDATE app_info
        SET app_img = %s,
            app_name_company = %s,
            app_version = %s,
            app_total_rate = %s,
            app_average_rate = %s,
            app_install = %s,
            app_category = %s,
            app_size = %s,
            app_last_update = %s,
            app_url = %s,
            app_img_base64 = %s
        WHERE app_id = %s;
        """
        cursor.execute(update_query, (
            data['App_Img'], data['App_Name_Company'], data['App_Version'],
            data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
            data['App_Category'], data['App_Size'], data['App_Last_Update'], 
            data['App_URL'], data['App_Img_Base64'], app_id
        ))
    else:
        # App doesn't exist, insert it into app_info
        insert_query = """
        INSERT INTO app_info (
            app_name, app_img, app_name_company, app_version, app_total_rate, 
            app_average_rate, app_install, app_category, app_size, app_last_update, 
            app_url, app_img_base64
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING app_id;
        """
        cursor.execute(insert_query, (
            data['App_Name'], data['App_Img'], data['App_Name_Company'], data['App_Version'],
            data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
            data['App_Category'], data['App_Size'], data['App_Last_Update'], 
            data['App_URL'], data['App_Img_Base64']
        ))
        app_id = cursor.fetchone()[0]  # Retrieve the new app_id after insertion
        # Reset the sequence after insert to ensure sequential IDs
    
    conn.commit()

    reset_query = """
    SELECT setval(pg_get_serial_sequence('app_info', 'app_id'), COALESCE(MAX(app_id), 1)) FROM app_info;
    """
    cursor.execute(reset_query)
    conn.commit()
    
    cursor.close()
    conn.close()
    return app_id


# Function to log each scrape with an explicit scraped_time
def log_scrape(data, app_id, app_scraped_time):
    conn = connect_db()
    cursor = conn.cursor()
    log_query = """
    INSERT INTO log_app (
        app_id, app_name, app_name_company, app_version, app_total_rate, 
        app_average_rate, app_install, app_category, app_size, 
        app_last_update, app_scraped_time, app_img
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute(log_query, (
        app_id, data['App_Name'], data['App_Name_Company'], data['App_Version'],
        data['App_Total_Rate'], data['App_Average_Rate'], data['App_Install'],
        data['App_Category'], data['App_Size'], data['App_Last_Update'], 
        app_scraped_time, data['App_Img']
    ))

    conn.commit()
    cursor.close()
    conn.close()


# Function to check if text contains Persian characters
def is_persian(text):
    """Checks if the text contains Persian characters."""
    return any("\u0600" <= char <= "\u06FF" for char in text)

# Retry with exponential backoff for driver.get
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
def load_page(driver, url):
    driver.get(url)

# Function to scrape app information
def give_information_app(app_name, url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--incognito")  

    # # Explicitly set the Chrome binary path
    # chrome_options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(options=chrome_options)
    # Set a longer page load timeout
    driver.set_page_load_timeout(350)

    retry_count = 0
    max_retries = 5  # Set a limit to retries

    while retry_count < max_retries:

        try:
            load_page(driver, url)
        except TimeoutException:
            print(f"Failed to load the page for app ID {app_name} after retries.")
            driver.quit()
            return

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'AppCommentsList__loadmore')))
        App_info_zone = driver.find_element(By.CLASS_NAME, 'AppDetails__col')
        App_Name = App_info_zone.find_element(By.CLASS_NAME, 'AppName').text

        if is_persian(App_Name):
            print("App information loaded in Persian.")
            break  # Exit the loop if the text is in Persian
        else:
            print("App information is in English; retrying...")
            retry_count += 1
            time.sleep(2)  # Wait a bit before retrying
            driver.refresh()  # Refresh the page

    if retry_count == max_retries:
        print(f"Failed to load Persian information for {url} after several attempts.")
    
    # Proceed with saving only if Persian content was detected
    if is_persian(App_Name):
        # Scrape the app details
        App_Name_Company = App_info_zone.find_element(By.CLASS_NAME, 'DetailsPageHeader__company').text
        App_Version = App_info_zone.find_element(By.CLASS_NAME, 'DetailsPageHeader__subtitles').text
        App_Install = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[0].text
        App_Total_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__title')[1].text
        App_Average_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[1].text
        App_Category = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[2].text
        App_Size = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[3].text
        App_Last_Update = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[4].text
        App_Img = App_info_zone.find_element(By.TAG_NAME, 'img').get_attribute('src')

        # Convert `app_img` to base64
        App_Img_Base64 = convert_image_to_base64(App_Img)

        # Format data for database insertion, including the URL

    driver.quit()
    APP_INFO = {
        'App_Name': App_Name,
        'App_Img': App_Img,
        'App_Name_Company': App_Name_Company,
        'App_Version': App_Version,
        'App_Total_Rate': App_Total_Rate,  # Correct spelling
        'App_Average_Rate': App_Average_Rate,
        'App_Install': App_Install,
        'App_Category': App_Category,
        'App_Size': App_Size,
        'App_Last_Update': App_Last_Update,
        'App_URL': url,
        'App_Img_Base64': App_Img_Base64
    }

    return APP_INFO

# Main loop to fetch URLs from the database and scrape them
def main():
    urls_to_crawl = fetch_urls_to_crawl() 
    app_scraped_time = datetime.now()  # Capture the current time when the scraping session starts
 
    for crawl_app_name, crawl_url in urls_to_crawl:
        print(f"Scraping {crawl_app_name} at {crawl_url}")
        app_data = give_information_app(crawl_app_name, crawl_url)

        if app_data:
            # Update app_info and retrieve the app_id
            app_id = get_or_create_app_id(app_data)

            # Log the scrape with the explicit scraped_time
            log_scrape(app_data, app_id, app_scraped_time)


if __name__ == "__main__":
    main()
