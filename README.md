# Sentiment_Analysis_Product
At first, in order to connect to pgadmin for checking and working with database through this tool, be sure pgadmin is connected with posgresql on docker.
For this manner, you should stop posgresql on your local system.
sudo service postgresql stop
## Run docker file
1) Build docker-compose

sudo docker-compose build

2) up every service

sudo docker-compose up app_scraper -d
sudo docker-compose logs -f app_scraper

