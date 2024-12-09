# Import packages
from datetime import datetime, date
from persiantools.jdatetime import JalaliDate
import psycopg2
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


# Database connection function
def connect_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    return conn


# Function to update Jalali dates for comments
def update_jalali_dates(app_id=None):
    conn = connect_db()
    cursor = conn.cursor()

    # SQL to fetch comments with missing Jalali dates
    query = """
        SELECT comment_id, comment_date 
        FROM public.comment
        WHERE (comment_date_jalali IS NULL OR comment_date_jalali = 0)
    """
    params = []
    if app_id:
        query += " AND app_id = %s"
        params.append(app_id)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No rows to update.")
        cursor.close()
        conn.close()
        return

    updates = []
    for comment_id, comment_date in rows:
        try:
            # Ensure `comment_date` is converted to `datetime.date` if necessary
            if isinstance(comment_date, str):
                comment_date = datetime.strptime(comment_date, "%Y-%m-%d").date()
            
            # Convert to Jalali and format as integer
            jalali_date = JalaliDate(comment_date)
            jalali_date_int = int(jalali_date.strftime("%Y%m%d"))  # Convert to integer in YYYYMMDD format
            updates.append((jalali_date_int, comment_id))
        except ValueError as e:
            print(f"Skipping invalid date {comment_date}: {e}")
        except Exception as e:
            print(f"Error converting date {comment_date}: {e}")

    if updates:
        try:
            cursor.executemany(
                "UPDATE public.comment SET comment_date_jalali = %s WHERE comment_id = %s;",
                updates,
            )
            conn.commit()
            print(f"Successfully updated {len(updates)} rows.")
        except Exception as e:
            print(f"Error updating Jalali dates: {e}")
    else:
        print("No valid dates to update.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    app_id = input("Enter app_id to test (or press Enter to process all): ").strip()
    app_id = int(app_id) if app_id else None
    update_jalali_dates(app_id)