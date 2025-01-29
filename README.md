# Sentiment_Analysis_Product

## Overview
Sentiment analysis is a crucial task in natural language processing (NLP) and large language models (LLMs). This project aims to analyze user sentiment towards banking applications by extracting and processing user comments from app stores.

The final goal is to build a dashboard for comparing customer sentiment across different banking applications and to provide data-driven recommendations through a recommender system. This enables managers and supervisors to make informed decisions for improving their products based on real user feedback.

## 📂 Project Structure
You can find the structure of the project in Wiki!

## Project Features
To achieve our goals, we have implemented the following steps:

### 1. Data Collection: Scraping Comments from Café Bazaar
We use Selenium to scrape user comments from Café Bazaar, a popular application marketplace.

### 2. Database Implementation
A PostgreSQL database is used to store and manage the collected data efficiently.

### 3. Text Preprocessing
We apply various preprocessing steps, including:

#### * Date Conversion: Converting Georgian dates to Jalali for better front-end usability.
#### * Text Cleaning: Removing unnecessary characters and normalizing Persian text.
#### * Encoding Images: Saving images as Base64 format for optimized storage.
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
This model is fine-tuned for Persian text sentiment analysis.
It classifies comments into one of the six sentiment categories above.
#### Transformer/DistilBERT (for additional filtering)
Since the mT5 model struggles to accurately detect "Mixed Sentiment" and "No Sentiment Expressed", we apply a second layer of analysis using DistilBERT.  
This additional model re-evaluates comments flagged as "Mixed" or "No Sentiment" to refine the classification and improve accuracy.  
Since Transformer-based models struggle with Persian text, we translate Persian comments to English before applying a second round of classification.  
By combining these two models, we enhance sentiment detection reliability and minimize misclassification errors.
### 5. Recommendation System
We extract useful insights from customer feedback by identifying common complaints and praises. Based on this, the system suggests improvements for banking applications.

### 6. Visualization & Dashboard
We provide a dashboard to help managers:

#### - Track user sentiment trends over time.
#### - Compare different banking applications.
#### - Gain actionable insights for decision-making.

## 📊 Dashboard Features  
📈 Track sentiment trends over time  
🏦 Compare banking applications  
📑 Generate reports for managers  
🔄 View daily scraping status  


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
```
tail -f logs/analyze_sentiment.log
```
Check scraper logs:  
```
tail -f logs/app_scraper_logging.log
```
Check daily tasks:  
```
tail -f logs/daily_task.log
```
### 🖧 RPC Communication
The RPC Server allows different components of the system to communicate efficiently.

#### 1️⃣ Start the RPC Server:
```
python RPC/RPC_server.py
```
#### 2️⃣ Test with an RPC Client:
```
python RPC/RPC_client.py
```
## 🤝 Contributing
If you have any suggestions to improve this repository, feel free to contact me...  
📧contact: mahdi.bahar.g@gmail.com
