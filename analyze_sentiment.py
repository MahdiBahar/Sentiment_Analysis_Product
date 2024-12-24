# Import libraries
from transformers import MT5ForConditionalGeneration, MT5Tokenizer, pipeline
import time
from googletrans import Translator
# Connect to database
from connect_to_database_func import connect_db
from dotenv import load_dotenv
from logging_config import setup_logger  # Import logger setup function

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger(name="sentiment_analysis", log_file="analyze_sentiment.log")

# Load the tokenizer and model
logger.info("Loading MT5 model and tokenizer...")
model_name = "persiannlp/mt5-base-parsinlu-sentiment-analysis"
tokenizer = MT5Tokenizer.from_pretrained(model_name)
model = MT5ForConditionalGeneration.from_pretrained(model_name)

# Load the second model (Hugging Face pipeline)
logger.info("Loading Hugging Face sentiment classifier...")
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

# Fetch comments that need sentiment analysis for a specific app
def fetch_comments_to_analyze(app_id):
    logger.info(f"Fetching comments for app_id: {app_id}")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            SELECT comment_id, comment_text, comment_rating
            FROM comment
            WHERE app_id = %s AND sentiment_score IS NULL;
        """
        cursor.execute(query, (app_id,))
        comments = cursor.fetchall()
        logger.info(f"Fetched {len(comments)} comments for analysis.")
        cursor.close()
        conn.close()
        return comments
    except Exception as e:
        logger.error(f"Error fetching comments: {e}", exc_info=True)
        return []

# Update the comment table with the sentiment result and sentiment score
def update_sentiment(comment_id, sentiment_result, sentiment_score, second_model_processed):
    # logger.info(f"Updating sentiment for comment_id: {comment_id}")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            UPDATE comment
            SET sentiment_result = %s, sentiment_score = %s, second_model_processed = %s
            WHERE comment_id = %s;
        """
        cursor.execute(query, (sentiment_result, sentiment_score, second_model_processed, comment_id))
        conn.commit()
        cursor.close()
        conn.close()
        # logger.info(f"Successfully updated comment_id: {comment_id}")
    except Exception as e:
        logger.error(f"Error updating sentiment for comment_id: {comment_id}: {e}", exc_info=True)

def run_model(context, text_b="نظر شما چیست", **generator_args):
    try:
        logger.debug(f"Running MT5 model for text: {context}")
        input_ids = tokenizer.encode(context + "<sep>" + text_b, return_tensors="pt")
        res = model.generate(input_ids, **generator_args)
        output = tokenizer.batch_decode(res, skip_special_tokens=True)

        if not output:
            raise ValueError("Model returned empty output.")
        logger.info(f"MT5 model output: {output[0]}")
        return output[0]
    except Exception as e:
        logger.error(f"Error in run_model: {e}", exc_info=True)
        return "no sentiment expressed"

def run_second_model(comment_text):
    try:
        logger.debug(f"Running second model for text: {comment_text}")
        translated_text = translator.translate(comment_text, dest="en").text
        if not translated_text:
            raise ValueError("Translation returned empty text.")
        
        result = classifier(translated_text)
        if not result or not isinstance(result, list):
            raise ValueError("Classifier returned invalid result.")
        
        logger.info(f"Second model output: {result[0]['label']}")
        return result[0]["label"]
    except Exception as e:
        logger.error(f"Error in run_second_model: {e}", exc_info=True)
        return "no sentiment expressed"

# Validate sentiment result and assign score
def validate_and_score_sentiment(sentiment_result):
    sentiment_result = sentiment_result.lower()
    if sentiment_result not in SENTIMENT_SCORES:
        sentiment_result = "no sentiment expressed"
    sentiment_score = SENTIMENT_SCORES[sentiment_result]
    logger.debug(f"Validated sentiment: {sentiment_result}, Score: {sentiment_score}")
    return sentiment_result, sentiment_score
# Main function to fetch comments for a specific app_id and update sentiments
def analyze_and_update_sentiment(comments, app_id):
    logger.info(f"Starting sentiment analysis for app_id: {app_id}")
    for comment_id, comment_text, comment_rating in comments:
        try:
            logger.info(f"Analyzing sentiment for comment_id: {comment_id}")
            sentiment_result = run_model(comment_text)
            second_model_processed = False
            # If the first model returns "non-sentiment", run the second model
            if sentiment_result.lower() in ["no sentiment expressed", "mixed", "neutral"]:
                logger.debug(f"Running second model for comment_id: {comment_id}")
                second_model_result = run_second_model(comment_text)

            # Apply conditional update logic based on second model result and rating
                if second_model_result == "NEGATIVE" and comment_rating == 1:
                    sentiment_result = "negative"
                    second_model_processed = True
                    print("second_model is used")
                elif second_model_result == "POSITIVE" and comment_rating == 5:
                    sentiment_result = "positive"
                    second_model_processed = True
                    print("second_model is used")
                # Otherwise, retain "no sentiment expressed"

            sentiment_result, sentiment_score = validate_and_score_sentiment(sentiment_result)
            update_sentiment(comment_id, sentiment_result, sentiment_score, second_model_processed)
            logger.info(f"Updated comment_id: {comment_id} with sentiment: {sentiment_result}, score: {sentiment_score}")
        except Exception as e:
            logger.error(f"Error processing comment_id: {comment_id}: {e}", exc_info=True)
            update_sentiment(comment_id, "Missed Value", 11, False)
            continue
        time.sleep(0.3)
