import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time

def place_basemap_order(aoi_geojson):
    PLANET_API_KEY = os.getenv('PLANET_API_KEY')
    if not PLANET_API_KEY:
        raise ValueError("No Planet API key found in environment variables")
    auth = HTTPBasicAuth(PLANET_API_KEY, '')
    headers = {
        'Content-Type': 'application/json',
    }
    # Basemap API URL
    BASEMAP_API_URL = 'https://api.planet.com/basemaps/v1/mosaics'
    basemapServiceResponse = requests.get(url=BASEMAP_API_URL, auth=auth)
    # Extract the mosaic names
    basemapServiceResponse.raise_for_status()
    if basemapServiceResponse.status_code != 204:
        basemaps = basemapServiceResponse.json()
        print("Basemaps: ", basemaps)
        print("Number of basemaps: ", len(basemaps))
        # does it matter?
        mosaic_name = basemaps['mosaics'][-1]['name']  # This selects the first basemap in the list
        print("selected mosaic is: ", mosaic_name)
        # Set the Orders API URL
        ORDERS_API_URL = 'https://api.planet.com/compute/ops/orders/v2'
        # Create the order parameters
        order_params = {
            "name": "Basemap order with geometry bbox",
            "source_type": "basemaps",
            "products": [
                {
                    "mosaic_name": mosaic_name,
                    "geometry": aoi_geojson
                }
            ]
        }
        # Send the POST request to create the order
        orderResponse = requests.post(ORDERS_API_URL, data=json.dumps(order_params), auth=auth, headers=headers)
        if orderResponse.status_code == 202:
            print("Order placed successfully")
            order_details = orderResponse.json()
            return order_details
        else:
            print("Failed to place order:", orderResponse.content)
            return None
    else:
        print('Failed to get basemaps:', basemapServiceResponse.status_code)
        return None

def poll_for_order_completion(order_id):
    ORDERS_API_URL = f'https://api.planet.com/compute/ops/orders/v2/{order_id}'
    PLANET_API_KEY = os.getenv('PLANET_API_KEY')
    if not PLANET_API_KEY:
        raise ValueError("No Planet API key found in environment variables")
    auth = HTTPBasicAuth(PLANET_API_KEY, '')
    while True:
        response = requests.get(ORDERS_API_URL, auth=auth)
        if response.status_code == 200:
            order_status = response.json()
            state = order_status['state']
            print(f"Current order state: {state}")
            if state == 'success':
                print("Order is ready for download.")
                return order_status
            elif state == 'failed':
                print("Order failed to process.")
                return None
        else:
            print(f"Failed to get order status: HTTP {response.status_code}")
            return None

        print("Waiting for 60 seconds before the next poll...")
        time.sleep(60)

def download_order_assets(order_details, download_folder):
     # Create download directory if it does not exist
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    # Loop through each file in the order
    for file_info in order_details['_links']['results']:
        file_url = file_info['location']
        file_name = file_info['name']
        file_name = file_name.replace('/', '_')
        file_path = os.path.join(download_folder, file_name)
        # Download the file
        print(f"Downloading {file_name}...")
        response = requests.get(file_url, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {file_name} to {file_path}")
        else:
            print(f"Failed to download {file_name}. Status code: {response.status_code}")

# midwest_aoi_geojson = {
#     "type": "Polygon",
#     "coordinates": [
#         [
#             [-104.057739, 41.000659], 
#             [-104.057739, 36.993076], 
#             [-80.518707, 36.993076],  
#             [-80.518707, 49.384358],  
#             [-89.100860, 49.384358],  
#             [-104.057739, 41.000659]  
#         ]
#     ]
# }

# the AOI for Illinois
# Failed to place order: 
# b'{"field":null,"general":[{"message":"Unable to accept order: geometry for mosaic global_monthly_2020_02_mosaic intersects 1004 quads, which exceeds the maximum per order of 500"}]}\n'
illinois_aoi_geojson = {
    "type": "Polygon",
    "coordinates": [
        [
            [-91.512974, 36.970298], 
            [-87.495199, 36.970298], 
            [-87.495199, 42.508338],  
            [-91.512974, 42.508338],  
            [-91.512974, 36.970298],  
        ]
    ]
}

test_geojson = {
    "type": "Polygon",
    "coordinates": [
        [
            [4.607406, 52.353994],
            [4.680005, 52.353994],
            [4.680005, 52.395523],
            [4.607406, 52.395523],
            [4.607406, 52.353994] 
        ]
    ]
}

# # Place the order for the basemap
# order_details = place_basemap_order(midwest_aoi_geojson)
# if order_details:
#     print(json.dumps(order_details, indent=2))

order_details = place_basemap_order(test_geojson)
if order_details:
    print(json.dumps(order_details, indent=2))
order_id = order_details["id"]
# order_status = poll_for_order_completion("92b416ed-9758-4289-a30d-7f84cbebfe4e")
order_status = poll_for_order_completion(order_id)
if order_status:
    print("completed")
    print(order_status)
    # Download the order assets
    download_folder = f'../test_urbana/test{order_id}'
    download_order_assets(order_status, download_folder)