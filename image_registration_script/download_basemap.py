import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time
import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
ORDERS_API_URL = 'https://api.planet.com/compute/ops/orders/v2'
BASEMAP_API_URL = 'https://api.planet.com/basemaps/v1/mosaics'
PLANET_API_KEY = os.getenv('PLANET_API_KEY')

# # TODO: ChatGPT wrote it, please double check
# def split_aoi(aoi_geojson, split_size):
#     """
#     Splits a large AOI into smaller segments.
#     :param aoi_geojson: A GeoJSON object representing the AOI.
#     :param split_size: The desired size of each segment.
#     :return: A list of smaller AOI segments as GeoJSON objects.
#     """
#     # Convert AOI to a GeoDataFrame
#     aoi_gdf = gpd.GeoDataFrame.from_features([aoi_geojson])
    
#     # Calculate the number of splits required based on the split size
#     total_area = aoi_gdf.area[0]
#     num_splits = int(np.ceil(total_area / split_size))
    
#     # Generate split AOIs
#     minx, miny, maxx, maxy = aoi_gdf.geometry[0].bounds
#     width = maxx - minx
#     height = maxy - miny

#     horizontal_splits = int(np.ceil(np.sqrt(num_splits * width / height)))
#     vertical_splits = int(np.ceil(num_splits / horizontal_splits))

#     # Create smaller AOI segments
#     smaller_aois = []
#     for i in range(horizontal_splits):
#         for j in range(vertical_splits):
#             # Calculate bounds for each segment
#             seg_minx = minx + i * width / horizontal_splits
#             seg_miny = miny + j * height / vertical_splits
#             seg_maxx = minx + (i + 1) * width / horizontal_splits
#             seg_maxy = miny + (j + 1) * height / vertical_splits
#             # Create a polygon for each segment
#             segment = Polygon([(seg_minx, seg_miny), (seg_maxx, seg_miny), (seg_maxx, seg_maxy), (seg_minx, seg_maxy)])
#             # Convert to GeoJSON format
#             segment_geojson = json.loads(gpd.GeoDataFrame(geometry=[segment], crs=aoi_gdf.crs).to_json())
#             smaller_aois.append(segment_geojson)
#     return smaller_aois

# def place_basemap_order(aoi_geojson):
#     print("type of aoi_geojson", type(aoi_geojson))
#     print("content of aoi_geojson", aoi_geojson)
#     if not PLANET_API_KEY:
#         raise ValueError("No Planet API key found in environment variables")
#     auth = HTTPBasicAuth(PLANET_API_KEY, '')
#     headers = {
#         'Content-Type': 'application/json',
#     }
#     basemapServiceResponse = requests.get(url=BASEMAP_API_URL, auth=auth)
#     # Extract the mosaic names
#     basemapServiceResponse.raise_for_status()
#     if basemapServiceResponse.status_code != 204:
#         basemaps = basemapServiceResponse.json()
#         # print("Basemaps: ", basemaps)
#         print("Number of basemaps: ", len(basemaps))
#         # does it matter?
#         mosaic_name = basemaps['mosaics'][-1]['name']  # This selects the first basemap in the list
#         print("selected mosaic is: ", mosaic_name)
#         # get the number of quads in this mosaic name
#         quad_ids = get_mosaic_quad_ids(mosaic_name)
#         quad_count = len(quad_ids)
#         print("number of quads", quad_count)
#         place_orders_for_quads(mosaic_name, quad_ids)
#         # Create the order parameters
#         order_params = {
#             "name": "Basemap order with geometry bbox",
#             "source_type": "basemaps",
#             "products": [
#                 {
#                     "mosaic_name": mosaic_name,
#                     "geometry": aoi_geojson['features'][0]['geometry']
#                 }
#             ]
#         }
#         # Send the POST request to create the order
#         orderResponse = requests.post(ORDERS_API_URL, data=json.dumps(order_params), auth=auth, headers=headers)
#         if orderResponse.status_code == 202:
#             print("Order placed successfully")
#             order_details = orderResponse.json()
#             return order_details
#         else:
#             print("Failed to place order:", orderResponse.content)
#             return None
#     else:
#         print('Failed to get basemaps:', basemapServiceResponse.status_code)
#         return None

def get_mosaic_name(aoi_geojson):
    print("type of aoi_geojson", type(aoi_geojson))
    print("content of aoi_geojson", aoi_geojson)
    if not PLANET_API_KEY:
        raise ValueError("No Planet API key found in environment variables")
    auth = HTTPBasicAuth(PLANET_API_KEY, '')
    headers = {
        'Content-Type': 'application/json',
    }
    basemapServiceResponse = requests.get(url=BASEMAP_API_URL, auth=auth)
    # Extract the mosaic names
    basemapServiceResponse.raise_for_status()
    if basemapServiceResponse.status_code != 204:
        basemaps = basemapServiceResponse.json()
        # print("Basemaps: ", basemaps)
        print("Number of basemaps: ", len(basemaps))
        # does it matter?
        mosaic_name = basemaps['mosaics'][-1]['name']  
    return mosaic_name

def place_orders_for_quads(mosaic_name, quad_ids, batch_size=500):
    order_ids = []
    auth = HTTPBasicAuth(PLANET_API_KEY, '')
    headers = {
        'Content-Type': 'application/json',
    }
    for i in range(0, len(quad_ids), batch_size):
        batch_quad_ids = quad_ids[i:i+batch_size]
        order_params = {
            "name": "Basemap order for specific quads",
            "source_type": "basemaps",
            "products": [{
                "mosaic_name": mosaic_name,
                "quad_ids": batch_quad_ids
            }]
        }
        response = requests.post(ORDERS_API_URL, data=json.dumps(order_params), auth=auth, headers=headers)
        if response.status_code == 202:
            print(f"Order placed successfully for batch starting at index {i}")
            order_details = response.json()
            order_ids.append(order_details["id"])
        else:
            print(f"Failed to place order for batch starting at index {i}: {response.content}")
    return order_ids

# def place_basemap_orders(aois):
#     order_details_list = []
#     for aoi_geojson in aois:
#         order_details = place_basemap_order(aoi_geojson)
#         if order_details:
#             order_details_list.append(order_details)
#     return order_details_list

def poll_for_order_completion(order_id):
    ORDERS_API_URL = f'https://api.planet.com/compute/ops/orders/v2/{order_id}'
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
        
def get_mosaic_quad_ids(mosaic_name):
    BASEMAP_API_URL = 'https://api.planet.com/basemaps/v1/mosaics'
    parameters = {"name__is": mosaic_name}
    auth = HTTPBasicAuth(PLANET_API_KEY, '')
    response = requests.get(BASEMAP_API_URL, params=parameters, auth=auth)
    if response.status_code == 200:
        basemaps = response.json()
        if basemaps['mosaics']:
            mosaic_id = basemaps['mosaics'][0]['id']
            # Extract bbox from mosaic metadata
            mosaic_bbox = basemaps['mosaics'][0]['bbox']
            string_bbox = ','.join(map(str, mosaic_bbox)) 
            print("bbox is: ", string_bbox)
            quads_url = f"{BASEMAP_API_URL}/{mosaic_id}/quads"
            quads_params = {'bbox': string_bbox}
            # download quad
            quads_response = requests.get(quads_url, params=quads_params, auth=auth)
            if quads_response.status_code == 200:
                quads_data = quads_response.json()
                # print(quads_data)
                quad_ids = [quad['id'] for quad in quads_data['items']]
                return quad_ids
            else:
                print("Failed to get quads information:", quads_response.content)
                return None
        else:
            print("No mosaics found with the provided name.")
            return None
    else:
        print("Failed to get mosaic metadata:", response.content)
        return None

        
def download_order_assets(order_details, download_folder):
     # Create download directory if it does not exist
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
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

# def process_basemap_order_and_download(aoi_geojson, split_size, base_download_path):
#     split_aois = split_aoi(aoi_geojson, split_size)
#     print("Aoi before split: ", aoi_geojson)
#     print("-----------------------------------------------------")
#     print("Aoi after split: ", split_aois)
#     # Place orders for each split AOI
#     all_order_details = place_basemap_orders(split_aois)
#     for order_details in all_order_details:
#         if order_details:
#             order_id = order_details["id"]
#             order_status = poll_for_order_completion(order_id)
#             if order_status and order_status['state'] == 'success':
#                 print(f"Order {order_id} completed. Downloading assets...")
#                 download_folder = os.path.join(base_download_path, f'order_{order_id}')
#                 download_order_assets(order_status, download_folder)
#             else:
#                 print(f"Order {order_id} failed or is incomplete.")

def process_basemap_order_and_download_by_quads(aoi_geojson, base_download_path):
    mosaic_name = get_mosaic_name(aoi_geojson)
    quad_ids = get_mosaic_quad_ids(mosaic_name)
    order_ids = place_orders_for_quads(mosaic_name, quad_ids)
    for order_id in order_ids:
        order_status = poll_for_order_completion(order_id)
        if order_status != None and order_status['state'] == 'success':
            print(f"Order {order_id} completed successfully.")
            # Specify the download folder for this order
            download_folder = os.path.join(base_download_path, f'order_{order_id}')
            download_order_assets(order_status, download_folder)
            return download_folder
    

if __name__ == "__main__":
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
    illinois_aoi_geojson_feature = {
        "type": "Feature",
        "properties": {},
        "geometry": illinois_aoi_geojson
    }

    split_size = 500  # Adjust based on the API's quad limit
    base_download_path = f'../test_urbana/test_illinois_basemap'
    download_folder = process_basemap_order_and_download_by_quads(illinois_aoi_geojson_feature, base_download_path)
    # process_basemap_order_and_download(illinois_aoi_geojson_feature, split_size, base_download_path)