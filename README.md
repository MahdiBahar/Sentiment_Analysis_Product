# Sentiment_Analysis_Product

## Overview
Sentiment analysis is a crucial task in natural language processing (NLP) and large language models (LLMs). This project aims to analyze user sentiment towards banking applications by extracting and processing user comments from app stores.

The final goal is to build a dashboard for comparing customer sentiment across different banking applications and to provide data-driven recommendations through a recommender system. This enables managers and supervisors to make informed decisions for improving their products based on real user feedback.

## Project Features
To achieve our goals, we have implemented the following steps:

### 1. Data Collection: Scraping Comments from Café Bazaar
We use Selenium to scrape user comments from Café Bazaar, a popular application marketplace.

### 2. Database Implementation
A PostgreSQL database is used to store and manage the collected data efficiently.

### 3. Text Preprocessing
We apply various preprocessing steps, including:

#### Date Conversion: Converting Georgian dates to Jalali for better front-end usability.
#### Text Cleaning: Removing unnecessary characters and normalizing Persian text.
#### Encoding Images: Saving images as Base64 format for optimized storage.
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

#### Track user sentiment trends over time.
#### Compare different banking applications.
#### Gain actionable insights for decision-making.

## Technical Details
### Using Docker for Deployment
To use pgAdmin with PostgreSQL inside Docker, ensure that your local PostgreSQL service is stopped before running the container.
For this manner, you should stop posgresql on your local system: 
```ruby
sudo service postgresql stop
```
## Run docker file
1) Build docker-compose
```ruby
sudo docker-compose build
```
2) up every service
```ruby
sudo docker-compose up app_scraper -d
sudo docker-compose logs -f app_scraper
```
## Contributing
If you have any suggestions to improve this repository, feel free to contact me:  
📧 mahdi.bahar.g@gmail.com
