import os
import re
import cv2
from image_registration_helper import *

def find_corresponding_metadata(tif_filename, directory_path):
    """Find the corresponding metadata JSON file for a given TIFF file based on satellite number."""
    base_filename = os.path.splitext(tif_filename)[0]
    metadata_filename = f"{base_filename}_metadata.json"
    metadata_filepath = os.path.join(directory_path, metadata_filename)
    if os.path.isfile(metadata_filepath):
        return metadata_filepath
    else:
        return None
    
def geo_reference_main(basemap_dir_path, image_path, image_metadata_path):
    best_match = None
    highest_iou = 0
    # Iterate through all .tif files in the basemap directory
    i = 0
    for filename in os.listdir(basemap_dir_path):
        # print(filename)
        if filename.endswith('.tif'):
            # print(filename)
            basemap_path = os.path.join(basemap_dir_path, filename)
            basemap_metadata_path = find_corresponding_metadata(filename, basemap_dir_path)
            print(basemap_path)
            print(basemap_metadata_path)
            if not basemap_metadata_path:
                continue
            H, registered_img, transformed_corners, basemap_original_dim = register_images(
                basemap_path, image_path, 0.75, 'bf', 50)
            #  overlay_images(basemap_path, registered_img, basemap_path_registered, 0.7)
            print("H is: ", H)
            if H is not None and registered_img is not None:
                registered_coors = transform_coordinates(basemap_metadata_path, transformed_corners, basemap_original_dim)
                ground_truth_coords = extract_coordinates(image_metadata_path)[:4]
                print("registered_coors", registered_coors)
                print("ground_truth_coords", ground_truth_coords)
                iou = compute_iou(registered_coors, ground_truth_coords)
                print("iou: ", iou)
                overlay_images(basemap_path, registered_img, f"{basemap_dir_path}/output_{iou}.jpg", 0.7)
                if iou > highest_iou:
                    best_match = basemap_path
                    highest_iou = iou
    # Log the best match result
    if best_match:
        print(f"Best match: {best_match} with IoU: {highest_iou}")
    else:
        print("No suitable match found.")

if __name__ == "__main__":
    basemap_dir_path = '../test_uiuc'
    image_path = '../test_urbana/20231213_163300_16_2473_3B_Visual.tif'
    image = cv2.imread(image_path)
    cv2.imwrite('../test_urbana/20231006_154454_21_2449_3B_Visual_clip.jpg', image)
    image_metadata_path = '../test_urbana/20231006_154454_21_2449_metadata.json'
    geo_reference_main(basemap_dir_path, image_path, image_metadata_path)
    
