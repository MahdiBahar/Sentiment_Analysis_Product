# Import libraries
import psycopg2
import os
from transformers import MT5ForConditionalGeneration, MT5Tokenizer, pipeline
import time
from googletrans import Translator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load the tokenizer and model
model_name = "persiannlp/mt5-base-parsinlu-sentiment-analysis"
tokenizer = MT5Tokenizer.from_pretrained(model_name)
model = MT5ForConditionalGeneration.from_pretrained(model_name)

# Load the second model (Hugging Face pipeline)
classifier = pipeline("sentiment-analysis")

# Initialize Google Translator
translator = Translator()

# Sentiment mapping for scoring
SENTIMENT_SCORES = {
    "very negative": -2,
    "negative": -1,
    "neutral": 0,
    "mixed": 0,
    "positive": 1,
    "very positive": 2,
    "no sentiment expressed": 0
}

# Database connection
def connect_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    return conn


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
  
    ###### AND sentiment_score IS NULL
    # ###LIMIT 100
    cursor.execute(query, (app_id,))
    comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return comments

# Update the comment table with the sentiment result and sentiment score
def update_sentiment(comment_id, sentiment_result, sentiment_score, second_model_processed):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        UPDATE comment 
        SET sentiment_result = %s, sentiment_score = %s , second_model_processed=%s 
        WHERE comment_id = %s;
    """
    cursor.execute(query, (sentiment_result, sentiment_score, second_model_processed, comment_id))
    conn.commit()
    cursor.close()
    conn.close()


def run_model(context, text_b="نظر شما چیست", **generator_args):
    try:
        input_ids = tokenizer.encode(context + "<sep>" + text_b, return_tensors="pt")
        res = model.generate(input_ids, **generator_args)
        output = tokenizer.batch_decode(res, skip_special_tokens=True)

        if not output:  # Check if the output is empty
            raise ValueError("Model returned empty output.")
        return output[0]
    except Exception as e:
        print(f"Error in run_model: {e}")
        return "no sentiment expressed"  # Fallback value



def run_second_model(comment_text):
    try:
        translated_text = translator.translate(comment_text, dest="en").text
        if not translated_text:  # Check if translation failed
            raise ValueError("Translation returned empty text.")
        
        result = classifier(translated_text)
        if not result or not isinstance(result, list):  # Validate classifier output
            raise ValueError("Classifier returned invalid result.")
        
        return result[0]["label"]  # Example output: "POSITIVE", "NEGATIVE", "NEUTRAL"
    except Exception as e:
        print(f"Error in run_second_model: {e}")
        return "no sentiment expressed"  # Fallback value


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
            continue

        for comment_id, comment_text, comment_rating in comments:
            try:
                sentiment_result = run_model(comment_text)
                second_model_processed=False
                # If the first model returns "non-sentiment", run the second model
                if (sentiment_result.lower() == "no sentiment expressed" or sentiment_result.lower() == "mixed" or sentiment_result.lower() == "neutral"):
                    
                    print(f"The current sentiment for this comment is {sentiment_result.lower()}")
                    second_model_result = run_second_model(comment_text)

                # Apply conditional update logic based on second model result and rating
                    if second_model_result == "NEGATIVE" and comment_rating == 1 :
                        sentiment_result = "negative"
                        second_model_processed= True
                        print("second_model is used")
                    elif second_model_result == "POSITIVE" and comment_rating == 5:
                        sentiment_result = "positive"
                        second_model_processed= True
                        print("second_model is used")
                    # Otherwise, retain "no sentiment expressed"

                sentiment_result, sentiment_score = validate_and_score_sentiment(sentiment_result)                
                update_sentiment(comment_id, sentiment_result, sentiment_score,second_model_processed)
                print(f"Updated comment {comment_id} for id {app_id} with sentiment: {sentiment_result}, score: {sentiment_score}")
            except Exception as e:
                print(f"Error processing comment {comment_id}: {e}")
                update_sentiment(comment_id, "Missed Value", 11, False)  # Assign fallback values
                continue
            # Add a delay between each analysis
            time.sleep(0.3)  # 300ms delay

if __name__ == "__main__":
    try:
        app_ids = list(map(int,os.getenv("APP_IDS","4").split(",")))
        print(f'app_ids = {app_ids}')
        # app_id = int(os.getenv("APP_ID", "28"))  # Fetch app_id from environment variables (default: 28)
        analyze_and_update_sentiment(app_ids)
    except KeyboardInterrupt:
        print("Script interrupted. Exiting gracefully....")