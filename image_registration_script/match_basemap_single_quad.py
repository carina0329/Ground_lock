import cv2
import numpy as np
import time
from image_registration_helper import *
# iou - best match is 1
# basemap test
# WSG 3857: How to query basemap
# output coordinates
basemap_path = '../test_urbana/basemap2.tif'
basemap_path_registered = '../test_urbana/basemap2_registered.jpg'
image_path = '../test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif'
H, registered_img, transformed_corners = register_images(basemap_path, image_path, 0.75, 'bf', 50)
if registered_img is not None:
    overlay_images(basemap_path, registered_img, basemap_path_registered, 0.5)