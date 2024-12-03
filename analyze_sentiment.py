import psycopg2
import os
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import time

# Load the tokenizer and model
model_name = "persiannlp/mt5-base-parsinlu-sentiment-analysis"
tokenizer = MT5Tokenizer.from_pretrained(model_name)
model = MT5ForConditionalGeneration.from_pretrained(model_name)

# Sentiment mapping for scoring
SENTIMENT_SCORES = {
    "very negative": -2,
    "negative": -1,
    "neutral": 0,
    "mixed": 0,
    "positive": 1,
    "very positive": 2,
    "no sentiment expressed": 10
}

# Database connection
def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "MEC-Sentiment"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )

# Fetch comments that need sentiment analysis for a specific app
def fetch_comments_to_analyze(app_id):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        SELECT comment_id, comment_text 
        FROM comment 
        WHERE app_id = %s 
        ;
    """
    ######AND sentiment_result IS NULL
    #########LIMIT 100
    cursor.execute(query, (app_id,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return comments

# Update the comment table with the sentiment result and sentiment score
def update_sentiment(comment_id, sentiment_result, sentiment_score):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        UPDATE comment 
        SET sentiment_result = %s, sentiment_score = %s 
        WHERE comment_id = %s;
    """
    cursor.execute(query, (sentiment_result, sentiment_score, comment_id))
    conn.commit()
    cursor.close()
    conn.close()

# Run the sentiment analysis model
def run_model(context, text_b="نظر شما چیست", **generator_args):
    input_ids = tokenizer.encode(context + "<sep>" + text_b, return_tensors="pt")
    res = model.generate(input_ids, **generator_args)
    output = tokenizer.batch_decode(res, skip_special_tokens=True)
    return output[0]

# Validate sentiment result and assign score
def validate_and_score_sentiment(sentiment_result):
    sentiment_result = sentiment_result.lower()  # Normalize the result
    if sentiment_result not in SENTIMENT_SCORES:
        # If result is irrelevant, assign it to "no sentiment expressed"
        sentiment_result = "no sentiment expressed"
    sentiment_score = SENTIMENT_SCORES[sentiment_result]
    return sentiment_result, sentiment_score

# Main function to fetch comments for a specific app_id and update sentiments
def analyze_and_update_sentiment(app_ids):
    
    for app_id in app_ids:
        print(f"Processing comments for app_id: {app_id}")
        comments = fetch_comments_to_analyze(app_id)
        if not comments:
            print("No more comments to analyze.")
            return

        for comment_id, comment_text in comments:
            try:
                sentiment_result = run_model(comment_text)
                sentiment_result, sentiment_score = validate_and_score_sentiment(sentiment_result)                
                update_sentiment(comment_id, sentiment_result, sentiment_score)
                print(f"Updated comment {comment_id} for id {app_id} with sentiment: {sentiment_result}, score: {sentiment_score}")
            except Exception as e:
                print(f"Error processing comment {comment_id}: {e}")

            # Add a delay between each analysis
            time.sleep(0.3)  # 300ms delay

if __name__ == "__main__":
    try:
        app_ids = list(map(int,os.getenv("APP_IDS","28").split(",")))
        # app_id = int(os.getenv("APP_ID", "28"))  # Fetch app_id from environment variables (default: 28)
        analyze_and_update_sentiment(app_ids)
    except KeyboardInterrupt:
        print("Script interrupted. Exiting gracefully....")
