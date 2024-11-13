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

# Function to get URLs from the `urls_to_crawl` table
def fetch_urls_to_crawl():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT crawl_app_name, crawl_url FROM public.url_to_crawl")
    urls = cursor.fetchall()
    cursor.close()
    conn.close()
    return urls


# Function to save data to PostgreSQL
def save_to_db(data):
    conn = connect_db()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO app_info (
        app_name, app_img, app_name_company, app_version, app_total_rate, 
        app_average_rate, app_install, app_category, app_size, app_last_update, app_url
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
    ON CONFLICT (app_name)
    DO UPDATE SET
        app_img = EXCLUDED.app_img,
        app_name_company = EXCLUDED.app_name_company,
        app_version = EXCLUDED.app_version,
        app_total_rate = EXCLUDED.app_total_rate,
        app_average_rate = EXCLUDED.app_average_rate,
        app_install = EXCLUDED.app_install,
        app_category = EXCLUDED.app_category,
        app_size = EXCLUDED.app_size,
        app_last_update = EXCLUDED.app_last_update,
          app_url = EXCLUDED.app_url;

    """
    cursor.execute(insert_query, (
        data['App_Name'], data['App_Img'], data['App_Name_Company'], data['App_Version'],
        data['App_Totoal_Rate'], data['App_Avrage_Rate'], data['App_Install'],
        data['App_Category'], data['App_Size'], data['App_Last_Update'], data['App_URL']
    ))
    conn.commit()

  # Reset the sequence after insert to ensure sequential IDs
    reset_query = """
    SELECT setval(pg_get_serial_sequence('app_info', 'app_id'), COALESCE(MAX(app_id), 1)) FROM app_info;
    """
    cursor.execute(reset_query)
    conn.commit()

    cursor.close()
    conn.close()


def is_persian(text):
    """Checks if the text contains Persian characters."""
    return any("\u0600" <= char <= "\u06FF" for char in text)


# Function to scrape app information
def give_information_app_first(app_name, url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--lang=fa")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--incognito")  

    driver = webdriver.Chrome(options=chrome_options)

    retry_count = 0
    max_retries = 5  # Set a limit to retries

    while retry_count < max_retries:

        driver.get(url)
    # Wait for page elements to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'AppCommentsList__loadmore')))
        App_info_zone = driver.find_element(By.CLASS_NAME, 'AppDetails__col')
        App_Name = App_info_zone.find_element(By.CLASS_NAME, 'AppName').text

# Check if the essential fields are in Persian
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
        App_Totoal_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__title')[1].text
        App_Avrage_Rate = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[1].text
        App_Category = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[2].text
        App_Size = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[3].text
        App_Last_Update = App_info_zone.find_elements(By.CLASS_NAME, 'InfoCube__content')[4].text
        App_Img = App_info_zone.find_element(By.TAG_NAME, 'img').get_attribute('src')

        # Format data for database insertion
        APP_INFO = {
            'App_Name': App_Name,
            'App_Img': App_Img,
            'App_Name_Company': App_Name_Company,
            'App_Version': App_Version,
            'App_Totoal_Rate': App_Totoal_Rate,
            'App_Avrage_Rate': App_Avrage_Rate,
            'App_Install': App_Install,
            'App_Category': App_Category,
            'App_Size': App_Size,
            'App_Last_Update': App_Last_Update,
            'App_URL': url  # Add the URL here
        }

    driver.quit()

    # Save data to PostgreSQL
    save_to_db(APP_INFO)

# Run the function

# Main loop to fetch URLs from the database and scrape them
def main():
    # Fetch URLs from the database
    urls_to_crawl = fetch_urls_to_crawl()  
    for crawl_app_name, crawl_url in urls_to_crawl:
        print(f"Scraping {crawl_app_name} at {crawl_url}")
        give_information_app_first(crawl_app_name, crawl_url)

if __name__ == "__main__":
    main()
