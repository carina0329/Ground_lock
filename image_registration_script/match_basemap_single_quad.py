import cv2
import numpy as np
import time
from image_registration_helper import *
# iou - best match is 1
# basemap test
# WSG 3857: How to query basemap
# output coordinates
# baseline - other paper that does image registration
# resolution, prior, satellite location
basemap_path = '../test_basemap/cfd6a60f-ec1e-491d-a885-e06d43990bd5/quad_819-3415.tif'
basemap_path_registered = '../test_urbana/basemap5_registered.jpg'
image_path = '../test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif'
image_metadata_path = '../test_urbana/20231006_154454_21_2449_metadata.json'
basemap_metadata_path = '../test_basemap/cfd6a60f-ec1e-491d-a885-e06d43990bd5/quad_819-3415_metadata.json'
H, registered_img, transformed_corners, basemap_original_dim = register_images(basemap_path, image_path, 0.75, 'bf', 50)
if registered_img is not None:
    overlay_images(basemap_path, registered_img, basemap_path_registered, 0.7)
    # geo_coors_basemap = extract_coordinates_basemap("../test_urbana/20231006_154454_21_2449_metadata.json")
    registered_coors = transform_coordinates(basemap_metadata_path, transformed_corners, basemap_original_dim)
    ground_truth_coords = extract_coordinates(image_metadata_path)
    # iou = compute_iou(registered_coors, ground_truth_coords)
    print("computed coordinates are: ", registered_coors, " ground truth coordinates are: ", ground_truth_coords)