import psycopg2
import os
import shutil  # For clearing cache
from transformers import MT5ForConditionalGeneration, MT5Tokenizer, pipeline
from googletrans import Translator

# Load the first model (MT5)
model_name = "persiannlp/mt5-base-parsinlu-sentiment-analysis"
tokenizer = MT5Tokenizer.from_pretrained(model_name)
model = MT5ForConditionalGeneration.from_pretrained(model_name)

# Load the second model (Hugging Face pipeline)
classifier = pipeline("sentiment-analysis")

# Initialize Google Translator
translator = Translator()

# Database connection
def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "MEC_Sentiment"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )

# Fetch a batch of comments for analysis
def fetch_comments_to_analyze(app_id, batch_size=50):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        SELECT comment_id, comment_text, comment_rating
        FROM comment
        WHERE app_id = %s AND sentiment_result IS NULL
        ORDER BY comment_id ASC
        LIMIT %s;
    """
    cursor.execute(query, (app_id, batch_size))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return comments

# Update the comment table with the sentiment result
def update_sentiment(comment_id, sentiment_result):
    conn = connect_db()
    cursor = conn.cursor()
    query = "UPDATE comment SET sentiment_result = %s WHERE comment_id = %s;"
    cursor.execute(query, (sentiment_result, comment_id))
    conn.commit()
    cursor.close()
    conn.close()

# Run the first model (MT5)
def run_first_model(context, text_b="نظر شما چیست", **generator_args):
    input_ids = tokenizer.encode(context + "<sep>" + text_b, return_tensors="pt")
    res = model.generate(input_ids, **generator_args)
    output = tokenizer.batch_decode(res, skip_special_tokens=True)
    return output[0]

# Run the second model (Hugging Face pipeline)
def run_second_model(comment_text):
    translated_text = translator.translate(comment_text, dest="en").text
    result = classifier(translated_text)
    return result[0]["label"]  # Example output: "POSITIVE", "NEGATIVE", "NEUTRAL"

# Clear Hugging Face cache
def clear_cache():
    cache_dir = os.getenv("HF_HOME", "/root/.cache/huggingface")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("Cache cleared.")

# Analyze and update sentiment for each batch
def analyze_and_update_sentiment(app_id, batch_size=50):
    while True:
        comments = fetch_comments_to_analyze(app_id, batch_size)
        if not comments:  # No more comments to process
            print(f"All comments for app_id {app_id} have been processed.")
            break

        for comment_id, comment_text, comment_rating in comments:
            try:
                sentiment_result = run_first_model(comment_text)

                # If the first model returns "no sentiment expressed", run the second model
                if sentiment_result.lower() == "no sentiment expressed":
                    second_model_result = run_second_model(comment_text)

                    # Apply conditional update logic based on second model result and rating
                    if second_model_result == "NEGATIVE" and comment_rating == 1:
                        sentiment_result = "negative"
                    elif second_model_result == "POSITIVE" and comment_rating == 5:
                        sentiment_result = "positive"
                    # Otherwise, retain "no sentiment expressed"

                update_sentiment(comment_id, sentiment_result)
                print(f"Updated comment {comment_id} with sentiment: {sentiment_result}")
            except Exception as e:
                print(f"Error processing comment {comment_id}: {e}")

        # Clear cache after processing each batch
        clear_cache()

if __name__ == "__main__":
    app_id = int(os.getenv("APP_ID", "28"))  # Fetch app_id from environment variables (default: 28)
    batch_size = int(os.getenv("BATCH_SIZE", "50"))  # Fetch batch size from environment variables (default: 50)
    analyze_and_update_sentiment(app_id, batch_size)
