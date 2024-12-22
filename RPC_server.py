from jsonrpc import JSONRPCResponseManager, dispatcher
from http.server import BaseHTTPRequestHandler, HTTPServer
from comment_scraper import fetch_app_urls_to_crawl, crawl_comments
from app_scraper_check import give_information_app, check_and_create_app_id
from analyze_sentiment import analyze_and_update_sentiment, fetch_comments_to_analyze

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = self.rfile.read(content_length).decode()
        
        response = JSONRPCResponseManager.handle(request, dispatcher)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.json.encode())


@dispatcher.add_method
def crawl_comment(app_ids):
    # app_ids = [28,31]
    apps = fetch_app_urls_to_crawl(app_ids)
    try:

        for app_id, app_url in apps:
            print(f"Crawling comments for app at {app_url}")
            crawl_comments(app_id, app_url)
        return {"status of crawling comments": "success", "app_id": app_id}
    
    except Exception as e:
        print(e)
        return {"status of crawling comments": "failed", "details of error" : e}

@dispatcher.add_method
def sentiment_analysis(app_ids):
    try:

        for app_id in app_ids:
            print(f"Processing comments for app_id: {app_id}")
            comments = fetch_comments_to_analyze(app_id)
            if not comments:
                print("No more comments to analyze.")

                return {"staus of sentiment analysis" : "no more comments to analyze" , "app_id": app_id}
                # continue
            analyze_and_update_sentiment(comments, app_id)

            return {"status of sentiment analysis": "success", "app_id":app_id}
    
    # except KeyboardInterrupt:
    except Exception as e:

        print(f"Script interrupted because {e}")
        return {"status of sentiment analysis": "failed", "details of error" : e}

# By considering getting nickname
@dispatcher.add_method
def check_add_url(crawl_url, crawl_app_nickname = 'unknown'):
    selected_domain = crawl_url.split('/')[2]

    if selected_domain == "cafebazaar.ir":
        app_data = give_information_app(crawl_app_nickname, crawl_url)
        report = check_and_create_app_id(app_data)
        print(report)
    else:
        report = f'The {crawl_url} is not related to Cafebazar or not valid. Please try again'
        print(report)
    return report

# Run server
if __name__ == "__main__":
    print("Server running on port 5000...")
    server = HTTPServer(("localhost", 5000), RequestHandler)
    server.serve_forever()
