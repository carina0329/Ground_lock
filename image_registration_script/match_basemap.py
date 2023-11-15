import cv2
import numpy as np
import time
from overlay import *
from transform_coordinates import *
# iou - best match is 1
# basemap test
# WSG 3857: How to query basemap
# output coordinates
def register_images(image1_path, image2_path, threshold, matcher_type, scale_percent=100):
    start_time = time.time()
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    cv2.imwrite('../test_urbana/basemap_original.jpg', img1)
    cv2.imwrite('../test_urbana/image_to_be_registered.jpg', img2)
    # change the depth of the bits
    if img1.dtype != np.uint8:
        # check max val
        img1 = np.uint8(img1 / 256)
    if img2.dtype != np.uint8:
        img2 = np.uint8(img2 / 256)
    (h, w) = img1.shape[:2]
    # reduce resolution
    width = int(img1.shape[1] * scale_percent / 100)
    height = int(img1.shape[0] * scale_percent / 100)
    dim = (width, height)
    img1 = cv2.resize(img1, dim, interpolation=cv2.INTER_AREA)
    img2 = cv2.resize(img2, dim, interpolation=cv2.INTER_AREA)
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    matcher = None
    if matcher_type == "bf":
        matcher = cv2.BFMatcher()
    elif matcher_type == "flann":
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    matches = matcher.knnMatch(des1, des2, k=2)
    good_matches = [m for m, n in matches if m.distance < threshold * n.distance]
    print("number of good matches detected", len(good_matches))
    ref = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    sensed = np.float32([kp2[m.trainIdx].pt for m in good_matches])
    H, status = cv2.findHomography(sensed, ref, cv2.RANSAC)
    h, w = img1.shape
    registered_img = cv2.warpPerspective(img2, H, (w, h))
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration:.2f} seconds")
    return registered_img, H

registered_img, H = register_images('../test_urbana/basemap2.tif', '../test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif', 0.75, "bf", scale_percent=50)
if registered_img is not None:
    cv2.imwrite('../test_urbana/basemap_test2_registered.jpg', registered_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    overlay_images('../test_urbana/basemap_original.jpg', '../test_urbana/basemap_test2_registered.jpg', 0.5)
    # transform_coordinates()