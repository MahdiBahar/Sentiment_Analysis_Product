from jsonrpc import JSONRPCResponseManager, dispatcher
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import uuid
from comment_scraper import fetch_app_urls_to_crawl, crawl_comments
from app_scraper_check import give_information_app, check_and_create_app_id
from analyze_sentiment import analyze_and_update_sentiment, fetch_comments_to_analyze


# Global dictionary to track tasks
tasks_status = {}
tasks_lock = threading.Lock()

# Event for synchronization
crawl_event = threading.Event()  # Signaled when crawling is complete


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = self.rfile.read(content_length).decode()
        response = JSONRPCResponseManager.handle(request, dispatcher)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.json.encode())


# Helper function to simulate long tasks
def perform_task(task_id, task_function, *args):
    global tasks_status

    # Update task status to "working"
    with tasks_lock:
        tasks_status[task_id] = {"status": "working", "description": tasks_status[task_id]["description"]}

    try:
        # Execute the actual task function
        task_function(*args)
        # Update task status to "completed"
        with tasks_lock:
            tasks_status[task_id]["status"] = "completed"
    except Exception as e:
        # Update task status to "failed"
        with tasks_lock:
            tasks_status[task_id] = {"status": "failed", "description": tasks_status[task_id]["description"], "error": str(e)}


@dispatcher.add_method
def crawl_comment(app_ids):
    global tasks_status, crawl_event

    crawl_event.clear()
    # Generate a unique task ID
    # task_id = str(uuid.uuid4())
    task_id = '1'

    # Immediately respond that the task has started
    with tasks_lock:
        tasks_status[task_id] = {"status": "started", "description": "Crawling comments"}

    # Start the task in a separate thread
    # Start the task in a separate thread
    def wrapped_task():
        try:
            fetch_and_crawl_comments(app_ids)
        finally:
            crawl_event.set()  # Signal that crawling is complete

    threading.Thread(target=perform_task, args=(task_id, wrapped_task)).start()


    # threading.Thread(target=perform_task, args=(task_id, fetch_and_crawl_comments, app_ids)).start()

    return {"task_id": task_id,"message": "Task started: Crawling comments"}


@dispatcher.add_method
def sentiment_analysis(app_ids):
    global tasks_status,crawl_event

    # Generate a unique task ID
    # task_id = str(uuid.uuid4())
    task_id = '2'
    # Immediately respond that the task has started
    with tasks_lock:
        tasks_status[task_id] = {"status": "started", "description": "Performing sentiment analysis"}

        # Start the task in a separate thread
    def wrapped_task():
        crawl_event.wait()  # Wait for crawling to complete
        analyze_sentiments(app_ids)
     
    threading.Thread(target=perform_task, args=(task_id, wrapped_task)).start()

    # Start the task in a separate thread
    # threading.Thread(target=perform_task, args=(task_id, analyze_sentiments, app_ids)).start()

    return {"task_id": task_id, "message": "Task started: Sentiment analysis"}


@dispatcher.add_method
def check_add_url(crawl_url, crawl_app_nickname='unknown'):
    # This method is lightweight and does not require asynchronous tracking
    selected_domain = crawl_url.split('/')[2]

    if selected_domain == "cafebazaar.ir":
        app_data = give_information_app(crawl_app_nickname, crawl_url)
        [long_report, short_report] = check_and_create_app_id(app_data)
        print(long_report)
    else:
        long_report = f"The {crawl_url} is not related to Cafebazar or not valid. Please try again"
        short_report = 'Bad-URL'
        print(long_report)
    return {"status": short_report, "message": long_report}


@dispatcher.add_method
def check_task_status(task_id):
    global tasks_status

    # Check the status of the given task
    with tasks_lock:
        if task_id in tasks_status:
            return tasks_status[task_id]
        else:
            return {"status": "error", "message": "Task ID not found"}


# Task-specific implementations
def fetch_and_crawl_comments(app_ids):
    print("Fetching app URLs and crawling comments...")
    apps = fetch_app_urls_to_crawl(app_ids)
    for app_id, app_url in apps:
        print(f"Crawling comments for app at {app_url}")
        crawl_comments(app_id, app_url)


def analyze_sentiments(app_ids):
    print("Analyzing sentiments...")
    for app_id in app_ids:
        comments = fetch_comments_to_analyze(app_id)
        if not comments:
            print(f"No comments left to analyze for app_id {app_id}")
            continue
        analyze_and_update_sentiment(comments, app_id)




# Run the server
if __name__ == "__main__":
    print("Server running on port 5000...")
    crawl_event.set()
    server = HTTPServer(("0.0.0.0", 5000), RequestHandler)
    server.serve_forever()
