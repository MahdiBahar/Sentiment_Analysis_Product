import requests
import time

def make_request(method, params):
    url = "http://localhost:5000"
    headers = {"Content-Type": "application/json"}

    # Construct the request payload
    request_payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    # Send the request to the server
    response = requests.post(url, headers=headers, json=request_payload)

    # Handle the response
    if response.status_code == 200:
        response_json = response.json()
        print("Full response:", response_json) 
        if "result" in response_json:
            return response_json["result"]
        elif "error" in response_json:
            raise Exception(f"RPC Error: {response_json['error']['message']}")
    else:
        raise Exception(f"HTTP Error: {response.status_code} - {response.text}")


def start_and_track_task(method, params=None):


    try:
        # Start the task
        result = make_request(method, params)
        if not result or "task_id" not in result:
            print(f"Failed to start task for method {method}")
            return

        task_id = result["task_id"]
        print(f"Task {method} started with task_id: {task_id}")

        # Track the progress of the task
        while True:
            status_result = make_request("check_task_status", {"task_id": task_id})
            print(f"Task {method} status: {status_result}")

            # Stop polling when the task is completed or failed
            if status_result and "status" in status_result and status_result["status"] in ("completed", "failed"):
                break

            # Wait before polling again
            time.sleep(100)

    except Exception as e:
        print(f"Error in {method}: {e}")


# crawl_url = 'https://cafebazaar.ir/app/com.pmb.mobile'
# crawl_url = 'https://cafebazaar.ir/app/com.bpm.social?l=fa'
crawl_url = 'https://cafebazaar.ir/app/ir.divar'
# crawl_url = 'https://cafebazaar.ir/app/ir.nasim?l=fa'

if __name__ == "__main__":
    app_ids = [23,24,25,26,27,28,29,30,31,32,33,34,35,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]  # Example app IDs
    # app_ids = [28]
    # app_ids = [8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]
    print("Starting crawl_comment task...")
    start_and_track_task("crawl_comment", {"app_ids": app_ids})

    print("\nStarting sentiment_analysis task...")
    start_and_track_task("sentiment_analysis", {"app_ids": app_ids})
    # result_check_add_url = make_request("check_add_url",{"crawl_url": crawl_url})
    # print(f"Result of check url to add or ignore is that {result_check_add_url}")


