

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
    print(f"----status : {response.status_code}")
    if response.status_code == 200:
        response_json = response.json()
        print("Full response:", response_json) 
        if "result" in response_json:
            return response_json["result"]
        elif "error" in response_json:
            raise Exception(f"RPC Error: {response_json['error']['message']}")
    else:
        raise Exception(f"HTTP Error: {response.status_code} - {response.text}")


#####Test 

# crawl_app_nickname ='squid game'
# crawl_url = 'https://cafebazaar.ir/app/com.defugames.survivegame'
# crawl_app_nickname = 'keyboard'
# crawl_url ='https://cafebazaar.ir/app/com.ziipin.softkeyboard.iran'

# crawl_app_nickname ='squid game'
# crawl_url = 'https://www.geeksforgeeks.org/postgresql-drop-table'
crawl_app_nickname= 'refah'
crawl_url= "https://cafebazaar.ir/app/com.refahbank.dpi.android"
# crawl_url = 'https://cafebazaar.ir/app/com.sibche.aspardproject.app'

# crawl_url = 'https://cafebazaar.ir/app/com.sibche.aspardproject.app'


if __name__ == "__main__":
    try:
        # app_ids = [28]  
        # result_comment_crawl = make_request("crawl_comment", {"app_ids": app_ids})
        # print(f"Result of crawl_comment: {result_comment_crawl}")
        
        # result_sentiment = make_request("sentiment_analysis", {"app_ids": app_ids})
        # print(f"Result of sentiment_comment: {result_sentiment}")
        
        result_check_add_url = make_request("check_add_url",{"crawl_app_nickname": crawl_app_nickname, "crawl_url": crawl_url})
        print(f"Result of check url to add or ignore is that {result_check_add_url}")

    except Exception as e:
        print(f"Error: {e}")

