# Libraries
from PIL import Image
import base64
import requests
from io import BytesIO


# # Function to download an image and convert it to a base64 string
# def convert_image_to_base64(image_url, last_base_64 = "NULL" ,size = (32,32)):
#     try:
#         response = requests.get(image_url)
#         # Check if the request was successful
#         response.raise_for_status()
#         # Open the image using Pillow
#         img = Image.open(BytesIO(response.content))  

#         # Resize the image
#         img_resized = img.resize(size, Image.Resampling.LANCZOS)

#         # Save the resized image to a BytesIO buffer
#         buffer = BytesIO()
#         img_resized.save(buffer, format="PNG")  # Save as PNG or another desired format
        
#         # Get the base64-encoded string
#         base64_img = base64.b64encode(buffer.getvalue()).decode('utf-8') 
#         return base64_img
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching image from {image_url}: {e}")
#         return last_base_64
#     except Exception as e:
#         print(f"Error processing image: {e}")
#         return last_base_64






def convert_image_to_base64(image_url,last_base_64= None):
    try:
        image_reduced_size = image_url.split("?")[0]+"?x-img=v1/resize,h_32,w_32,lossless_false/optimize"
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

