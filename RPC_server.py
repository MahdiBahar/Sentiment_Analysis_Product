from jsonrpc import JSONRPCResponseManager, dispatcher
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from comment_scraper import fetch_app_urls_to_crawl, crawl_comments
from app_scraper_check import give_information_app, check_and_create_app_id
from analyze_sentiment import analyze_and_update_sentiment, fetch_comments_to_analyze

# Global variable to track i server is busy or not
is_busy = threading.Lock()
current_task = None

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

    global is_busy , current_task

    # Try to acquire the lock to check if the server is busy
    if not is_busy.acquire(blocking=False):
        return {"status": "busy", "message": f"Server is currently processing another request : {current_task}"}

    current_task = "crawl_comment"

    try:
        print("Starting crawling comments")
        apps = fetch_app_urls_to_crawl(app_ids)
        for app_id, app_url in apps:
            print(f"Crawling comments for app at {app_url}")
            crawl_comments(app_id, app_url)
        return {"status of crawling comments": "success", "app_id": app_id}
    
    except Exception as e:
        print(e)
        return {"status of crawling comments": "failed", "details of error" : e}
    finally:
        current_task = None
        is_busy.release()


@dispatcher.add_method
def sentiment_analysis(app_ids):

    global is_busy , current_task
    # Try to acquire the lock to check if the server is busy
    if not is_busy.acquire(blocking=False):
        return {"status": "busy", "message": f"Server is currently processing another request: {current_task}"}

    current_task = "sentiment_analysis"

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
    finally:
        current_task = None
        is_busy.release()



# By considering getting nickname
@dispatcher.add_method
def check_add_url(crawl_url, crawl_app_nickname = 'unknown'):

    global current_task

    selected_domain = crawl_url.split('/')[2]

    current_task = "add_url"
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
