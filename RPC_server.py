from jsonrpc import JSONRPCResponseManager, dispatcher
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from comment_scraper import fetch_app_urls_to_crawl, crawl_comments
from analyze_sentiment import analyze_and_update_sentiment

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
    for app_id, app_url in apps:
        print(f"Crawling comments for app at {app_url}")
        crawl_comments(app_id, app_url)
    
    return {"status": "success", "app_id": app_id}


@dispatcher.add_method
def sentiment_analysis(app_ids):
    try:

        analyze_and_update_sentiment(app_ids)
    except KeyboardInterrupt:
        print("Script interrupted. Exiting gracefully....")

    return {"status of sentiment analysis": "success"}




# Run server
if __name__ == "__main__":
    print("Server running on port 5000...")
    server = HTTPServer(("localhost", 5000), RequestHandler)
    server.serve_forever()
