import os
import json
import cv2
from image_registration_helper import *

def find_corresponding_metadata(tif_filename, directory_path):
    """Find the corresponding metadata JSON file for a given TIFF file."""
    base_name = os.path.splitext(tif_filename)[0]
    base_name = base_name.split('_')
    metadata_filename = f"{base_name}_metadata.json"
    # metadata_path = os.path.join(directory_path, metadata_filename)
    # print(metadata_path)
    if os.path.exists(metadata_filename):
        return metadata_filename
    else:
        print(f"Metadata file does not exist for {tif_filename}")
        return None

def geo_reference_main(basemap_dir_path, image_path, image_metadata_path):
    best_match = None
    highest_iou = 0
    # Iterate through all .tif files in the basemap directory
    for filename in os.listdir(basemap_dir_path):
        # print(filename)
        if filename.endswith('.tif'):
            print(filename)
            basemap_path = os.path.join(basemap_dir_path, filename)
            basemap_metadata_path = find_corresponding_metadata(filename, basemap_dir_path)
            if not basemap_metadata_path:
                continue
            H, registered_img, transformed_corners, basemap_original_dim = register_images(
                basemap_path, image_path, 0.75, 'bf', 50)
            print("H is: ", H)
            if registered_img is not None:
                registered_coors = transform_coordinates(basemap_metadata_path, transformed_corners, basemap_original_dim)
                ground_truth_coords = extract_coordinates(image_metadata_path)
                iou = compute_iou(registered_coors, ground_truth_coords)
                if iou > highest_iou:
                    best_match = basemap_path
                    highest_iou = iou
    # Log the best match result
    if best_match:
        print(f"Best match: {best_match} with IoU: {highest_iou}")
    else:
        print("No suitable match found.")

if __name__ == "__main__":
    basemap_dir_path = '../test_urbana/test_illinois_basemap/order_d9b468ea-e1c9-491a-9b00-4e91f03ae4f1'
    image_path = '../test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif'
    image_metadata_path = '../test_urbana/20231006_154454_21_2449_metadata.json'
    geo_reference_main(basemap_dir_path, image_path, image_metadata_path)
