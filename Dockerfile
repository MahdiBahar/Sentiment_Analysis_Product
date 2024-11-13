
#Use the official Python image
FROM python:3.12.4

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set display port to avoid crash
ENV DISPLAY=:99

# Set environment variables for PostgreSQL connection
ENV DB_HOST=localhost
ENV DB_NAME=MEC_Sentiment
ENV DB_USER=postgres
ENV DB_PASS=postgres
ENV DB_PORT=5432

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set entry point
CMD ["python", "app_scraper.py"]