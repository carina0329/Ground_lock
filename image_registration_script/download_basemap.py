import requests
from requests.auth import HTTPBasicAuth
import json
import os
import time
import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
from shapely.geometry import shape, box

#%%
ORDERS_API_URL = 'https://api.planet.com/compute/ops/orders/v2'
BASEMAP_API_URL = 'https://api.planet.com/basemaps/v1/mosaics'
SERIES_API_URL = 'https://api.planet.com/basemaps/v1/series'
PLANET_API_KEY = os.getenv('PLANET_API_KEY')

#%%
def get_desired_mosaic(auth):
    desired_mosaic = []
    parameter = {"name__is" : "Global Monthly"}
    basemapSeriesServiceResponse = requests.get(url=SERIES_API_URL, auth=auth, params=parameter)
    mosaic_series_url = basemapSeriesServiceResponse.json()["series"][0]['_links']['mosaics']
    mosaics_series_list = requests.get(mosaic_series_url).json()['mosaics']
    for mosaic in mosaics_series_list:
        if "2021_07" in mosaic['name']:
            desired_mosaic.append(mosaic)
    return desired_mosaic
#%%
def get_api_response(auth):
    parameter = {"name__contains" : "global_monthly_2022_06_mosaic"}
    basemapServiceResponse = requests.get(url=BASEMAP_API_URL, auth=auth, params=parameter)
    print(basemapServiceResponse.text)
    # Extract the mosaic names
    basemapServiceResponse.raise_for_status()
    if basemapServiceResponse.status_code != 204:
        basemaps = basemapServiceResponse.json()
    return basemaps
#%%
def fetch_all_mosaics(api_url, aoi_geojson, auth):
    filtered_mosaics = []
    aoi_shape = shape(aoi_geojson['geometry'])
    print(aoi_shape)
    while api_url:
        response = requests.get(api_url, auth=auth)
        if response.status_code != 200:
            break
        data = response.json()
        for mosaic in data.get('mosaics', []):
            mosaic_bbox = mosaic['bbox']
            print(mosaic[''])
            # print(mosaic_bbox)
            # print("\n")
            mosaic_box = box(*mosaic_bbox)
            if aoi_shape.intersects(mosaic_box):
                print(aoi_shape)
                print("--------------")
                print(mosaic_box)
                print("................")
                filtered_mosaics.append(mosaic)
        api_url = data['_links'].get('_next')
    print(len(filtered_mosaics))
    return filtered_mosaics

def place_orders_for_quads(mosaic_name, quad_ids, headers, auth, batch_size=500):
    order_ids = []
    for i in range(0, len(quad_ids), batch_size):
        batch_quad_ids = quad_ids[i: i+batch_size]
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

def download_champaign_basemap():
    mosaic_dir = "../test_uiuc"
    champaign_quad_download_url = "https://api.planet.com/basemaps/v1/mosaics/e0c03fb4-0820-4ff8-be26-06cbaef9a7a7/quads?api_key=PLAKba683d39cadc42c4bd3388cfa6836a1d&bbox=-88.2775,40.0925,-88.1900,40.1260"
    quads_data = requests.get(champaign_quad_download_url, auth=auth, stream=True).json()
    for quad in quads_data['items']:
        quad_download_url = quad['_links']['download']
        quad_response = requests.get(quad_download_url, auth=auth, stream=True)
        quad_filename = f"quad_{quad['id']}.tif"
        quad_metadata_filename = f"quad_{quad['id']}_metadata.json"
        if quad_response.status_code == 200:
            with open(os.path.join(mosaic_dir, quad_filename), 'wb') as f:
                for chunk in quad_response.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            print(f"Downloaded quad {quad['id']} to {mosaic_dir}/{quad_filename}")
            with open(os.path.join(mosaic_dir, quad_metadata_filename), 'w') as f:
                json.dump(quad, f, indent=4)
            print(f"Saved metadata for quad {quad['id']} to {mosaic_dir}/{quad_metadata_filename}")
        else:
            print(f"Failed to download quad {quad['id']}")
#%%      
def download_quads_and_metadata(mosaic_list, auth, base_dir='mosaic_downloads'):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    for mosaic in mosaic_list:
        mosaic_dir = os.path.join(base_dir, mosaic['id'])
        os.makedirs(mosaic_dir, exist_ok=True)
        quads_url = mosaic['_links']['quads'].format(lx=mosaic['bbox'][0], ly=mosaic['bbox'][1], ux=mosaic['bbox'][2], uy=mosaic['bbox'][3])
        # Fetch the list of quads
        print(quads_url)
        while quads_url:
            quads_response = requests.get(quads_url, auth=auth)
            if quads_response.status_code != 200:
                print(f"Failed to fetch quads for mosaic {mosaic['id']}: {quads_response.content}")
                continue
            quads_data = quads_response.json()
            # Download each quad and its metadata
            for quad in quads_data['items']:
                quad_download_url = quad['_links']['download']
                quad_response = requests.get(quad_download_url, auth=auth, stream=True)
                quad_filename = f"quad_{quad['id']}.tif"
                quad_metadata_filename = f"quad_{quad['id']}_metadata.json"
                if quad_response.status_code == 200:
                    with open(os.path.join(mosaic_dir, quad_filename), 'wb') as f:
                        for chunk in quad_response.iter_content(chunk_size=1024):
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                    print(f"Downloaded quad {quad['id']} to {mosaic_dir}/{quad_filename}")
                    with open(os.path.join(mosaic_dir, quad_metadata_filename), 'w') as f:
                        json.dump(quad, f, indent=4)
                    print(f"Saved metadata for quad {quad['id']} to {mosaic_dir}/{quad_metadata_filename}")
                else:
                    print(f"Failed to download quad {quad['id']}")
            quads_url = quads_data['_links'].get('_next')
#%%
if __name__ == "__main__":
    if not PLANET_API_KEY:
        raise ValueError("No Planet API key found in environment variables")
    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    # illinois_aoi_geojson = {
    #     "type": "Polygon",
    #     "coordinates": [
    #         [
    #             [-91.512974, 36.970298], 
    #             [-87.495199, 36.970298], 
    #             [-87.495199, 42.508338],  
    #             [-91.512974, 42.508338],  
    #             [-91.512974, 36.970298],  
    #         ]
    #     ]
    # }
    # illinois_aoi_geojson_feature = {
    #     "type": "Feature",
    #     "properties": {},
    #     "geometry": illinois_aoi_geojson
    # }
   
    urbana_champaign_aoi_geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                [-88.2775, 40.0925],  # Southwest corner
                [-88.1900, 40.0925],  # Southeast corner
                [-88.1900, 40.1260],  # Northeast corner
                [-88.2775, 40.1260],  # Northwest corner
                [-88.2775, 40.0925],  # Back to Southwest corner
            ]
        ]
    }
    urbana_champaign_aoi_geojson_feature = {
        "type": "Feature",
        "properties": {},
        "geometry": urbana_champaign_aoi_geojson
    }
    headers = {
        'Content-Type': 'application/json',
    }

    # base_download_path = f'../test_urbana/test_urbana_champaign_basemap'
    # download_folder = process_basemap_order_and_download_by_quads(urbana_champaign_aoi_geojson_feature, base_download_path)
    # basemap_desired = get_desired_mosaic(auth)
    # # basemaps_filtered = filter_mosaics_by_aoi(basemaps, urbana_champaign_aoi_geojson_feature)
    # # basemaps_filtered = fetch_all_mosaics(BASEMAP_API_URL, urbana_champaign_aoi_geojson_feature, auth)
    # download_quads_and_metadata(basemap_desired, auth, '../test_basemap_2021_07')
    # download_champaign_basemap()