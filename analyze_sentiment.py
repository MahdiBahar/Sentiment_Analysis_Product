import psycopg2
import os
from transformers import MT5ForConditionalGeneration, MT5Tokenizer,pipeline
from googletrans import Translator


# Load the tokenizer and model
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

# Fetch comments that need sentiment analysis for a specific app
def fetch_comments_to_analyze(app_id):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        SELECT comment_id, comment_text , comment_rating
        FROM comment 
        WHERE app_id = %s  
        ;
    """
    ##########AND sentiment_result IS NULL
    ####### LIMIT 100

    cursor.execute(query, (app_id,))
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

# Run the sentiment analysis model
def run_model(context, text_b="نظر شما چیست", **generator_args):
    input_ids = tokenizer.encode(context + "<sep>" + text_b, return_tensors="pt")
    res = model.generate(input_ids, **generator_args)
    output = tokenizer.batch_decode(res, skip_special_tokens=True)
    return output[0]

# Run the second model (Hugging Face pipeline)
def run_second_model(comment_text):
    translated_text = translator.translate(comment_text, dest="en").text
    result = classifier(translated_text)
    return result[0]["label"]  # Example output: "POSITIVE", "NEGATIVE", "NEUTRAL"



# Main function to fetch comments for a specific app_id and update sentiments
def analyze_and_update_sentiment(app_id):
    comments = fetch_comments_to_analyze(app_id)
    for comment_id, comment_text, comment_rating in comments:
        try:
            sentiment_result = run_model(comment_text)

            # If the first model returns "non-sentiment", run the second model
            if sentiment_result.lower() == "no sentiment expressed":
                second_model_result = run_second_model(comment_text)

             # Apply conditional update logic based on second model result and rating
                if second_model_result == "NEGATIVE" and comment_rating == 1 :
                    sentiment_result = "negative"
                elif second_model_result == "POSITIVE" and comment_rating == 5:
                    sentiment_result = "positive"
                # Otherwise, retain "no sentiment expressed"




            update_sentiment(comment_id, sentiment_result)
            print(f"Updated comment {comment_id} with sentiment: {sentiment_result}")
        except Exception as e:
            print(f"Error processing comment {comment_id}: {e}")

if __name__ == "__main__":
    app_id = int(os.getenv("APP_ID", "28"))  # Fetch app_id from environment variables (default: 1)
    analyze_and_update_sentiment(app_id)



