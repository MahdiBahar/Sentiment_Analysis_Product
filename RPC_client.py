

import requests
import json

def make_request(method, params):
    url = "http://localhost:5000"
    headers = {"Content-Type": "application/json"}
    
    # Constructing the request payload
    request_payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    # Sending the request to the server
    response = requests.post(url, headers=headers, json=request_payload)
    
    # Handling the response
    if response.status_code == 200:
        response_json = response.json()
        print("Full response:", response_json) 
        if "result" in response_json:
            return response_json["result"]
        elif "error" in response_json:
            raise Exception(f"RPC Error: {response_json['error']['message']}")
    else:
        raise Exception(f"HTTP Error: {response.status_code} - {response.text}")



if __name__ == "__main__":
    try:
        app_ids = [9,10,11,12,13,14,15]  
        result_comment_crawl = make_request("crawl_comment", {"app_ids": app_ids})
        print(f"Result of crawl_comment: {result_comment_crawl}")
        result_sentiment = make_request("sentiment_analysis", {"app_ids": app_ids})
        print(f"Result of crawl_comment: {result_sentiment}")
    except Exception as e:
        print(f"Error: {e}")

