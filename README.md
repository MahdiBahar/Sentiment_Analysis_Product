# Sentiment_Analysis_Product

## Overview
Sentiment analysis is a crucial task in natural language processing (NLP) and large language models (LLMs). This project aims to analyze user sentiment towards banking applications by extracting and processing user comments from app stores.

The final goal is to build a dashboard for comparing customer sentiment across different banking applications and to provide data-driven recommendations through a recommender system. This enables managers and supervisors to make informed decisions for improving their products based on real user feedback.

## 📂 Project Structure
You can find the structure of the project in Wiki!

## Project Features
To achieve our goals, we have implemented the following steps:

### 1. Data Collection: Scraping Comments from Café Bazaar
We use Selenium to scrape user comments from Café Bazaar, a popular application marketplace. This allows us to collect real-time customer feedback for analysis.

### 2. Database Implementation
A PostgreSQL database is used to store and manage the collected data efficiently. The database structure is designed to handle:  
- App information (name, ratings, category, etc.)  
- User comments (text, sentiment, timestamps)  
- Logging and tracking updates  
### 3. Text Preprocessing
To improve data quality and ensure accurate analysis, we apply various preprocessing steps, including:

📅 Date Conversion: Converting Georgian dates to Jalali for better front-end usability.  
📝 Text Cleaning: Removing unnecessary characters and normalizing Persian text.  
🖼️ Encoding Images: Saving images as Base64 format for optimized storage.  

### 4. Sentiment Analysis
For sentiment classification, we utilize Persian NLP models to categorize user comments into six sentiment classes:  
✅ Positive  
✅ Very Positive  
❌ Negative  
❌ Very Negative  
⚖ Mixed Sentiment  
🔍 No Sentiment Expressed

### Models Used
#### "Persiannlp/mt5-base-parsinlu-sentiment-analysis"
 - This model is fine-tuned for Persian text sentiment analysis.
 - It classifies comments into one of the six sentiment categories above.
#### Transformer/DistilBERT (for additional filtering)
 - Since the mT5 model struggles to accurately detect "Mixed Sentiment" and "No Sentiment Expressed", we apply a second layer of analysis using DistilBERT.  
 - This additional model re-evaluates comments flagged as "Mixed" or "No Sentiment" to refine the classification and improve accuracy.
 - Since Transformer-based models struggle with Persian text, we translate Persian comments to English before applying a second round of classification.

##### By combining these two models, we enhance sentiment detection reliability and minimize misclassification errors.

### 5. Daily app update   
We run a scheduled task to update all existing app information daily. The system:  

 - Checks and collects updated app data automatically.  
 - Maintains a log table to store historical updates for tracking changes over time.
### 6.Logging system   
An organized logging system is implemented to track:  

✅ Tasks (such as scraping and analysis)  
❗ Errors and warnings  
🔄 System updates  
All logs are stored in the logs folder for easy debugging and monitoring.  

### 7. Using RPC (Remote Procedure Call)
One of the crucial aspects of the project is how the AI engine communicates with the Front-End client.  

 - We use an RPC server for client-server communication.  
 - This allows real-time task tracking, enabling the client to:  
 - Monitor task status (e.g., scraping progress).  
 - Send task requests (e.g., trigger sentiment analysis).  

### 8. Multi-threading
In some cases, the server is busy processing tasks while the client sends a request to check task status.  
To avoid blocking requests, we implemented multi-threading, allowing the server to:  

 - Run multiple tasks in parallel.  
 - Respond to client requests in real-time without delays.  

### 9. Automatic retry & error handling.  
During scraping and sentiment analysis, various issues such as:  

 - Network failures  
 - Timeout errors  
 - Unexpected data formats  
could interrupt the process. To handle these gracefully, we implemented:  
 - Retry mechanisms to automatically reattempt failed operations.  
 - Detailed error logging for debugging and diagnostics.  

### 10. Recommendation System
We extract useful insights from customer feedback by identifying:  
 - Common complaints and praises.  
 - Trends in user sentiment.  
Based on this, the system suggests improvements for banking applications, helping managers enhance user experience.  

### 11. Visualization & Dashboard
We provide a dashboard to help managers make better decision.
####  Dashboard Features  
📈 Track sentiment trends over time  
🏦 Compare banking applications  
📑 Get sentiment analysis and scrapping whenever the operator wants  
🔄 View daily scraping status   
📊 Generate reports for managers  


## Technical Details


### ⚡ Installation & Setup
#### 1️⃣ Install Dependencies  
First, install all required packages:
```ruby
pip install -r config/requirements.txt
```
#### 2️⃣ Set Up Environment Variables  
Create a .env file inside the config/ directory and configure:
```ruby
DB_HOST="enter your host"
DB_NAME="enter your database name"
DB_USER="enter your database user"
DB_PASS="enter the password of database"
DB_PORT="enter port to connect to the database"
```
### 3️⃣ Using Docker for Deployment 
#### 1️Stop PostgreSQL (if running locally):
To use pgAdmin with PostgreSQL inside Docker, ensure that your local PostgreSQL service is stopped before running the container.
For this purpose, you should stop posgresql on your local system: 
```ruby
sudo service postgresql stop
```
#### 2️ Build and start services:
```ruby
sudo docker-compose build
sudo docker-compose up app_scraper -d
```
#### 3️ Monitor logs:
```ruby
sudo docker-compose logs -f app_scraper
```

### 📜 Log Monitoring  
Since logging is a key feature in your project, here’s a guide to monitoring logs:

Check sentiment analysis logs:  
```ruby
tail -f logs/analyze_sentiment.log
```
Check scraper logs:  
```ruby
tail -f logs/app_scraper_logging.log
```
Check daily tasks:  
```ruby
tail -f logs/daily_task.log
```
### 🖧 RPC Communication
The RPC Server allows different components of the system to communicate efficiently.

#### 1️⃣ Start the RPC Server:
```ruby
python RPC/RPC_server.py
```
#### 2️⃣ Test with an RPC Client:
```ruby
python RPC/RPC_client.py
```
## 🤝 Contributing
If you have any suggestions to improve this repository, feel free to contact me...  
📧contact: mahdi.bahar.g@gmail.com
