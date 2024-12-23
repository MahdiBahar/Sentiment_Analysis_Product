# Libraries
import base64
import requests
from io import BytesIO

def convert_image_to_base64(image_url,last_base_64= None , size_h=32, size_w=32):
    try:
        image_reduced_size = image_url.split("?")[0]+f"?x-img=v1/resize,h_{size_h},w_{size_w},lossless_false/optimize"
        # image_reduced_size = image_url
        response = requests.get(image_reduced_size)
        # Check if the request was successful
        response.raise_for_status()  
        # Read image data as bytes
        img_data = BytesIO(response.content)  
        # Encode to base64 and decode to string
        base64_img = base64.b64encode(img_data.getvalue()).decode('utf-8')  
        return base64_img
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return last_base_64

