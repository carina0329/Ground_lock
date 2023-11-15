import cv2
import numpy as np
import time
from overlay import *
from transform_coordinates import *
# iou - best match is 1
# basemap test
# WSG 3857: How to query basemap
# output coordinates
def crop_and_rotate_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
     # for initial testing: rotate img to make sure it's correct
    (h, w) = img.shape[:2]
    center = (w / 2, h / 2)
    # Set the angle of rotation
    angle = 45 
    # Get the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Perform the rotation
    rotated = cv2.warpAffine(img, M, (w, h))
    cropped_rotated = rotated[320:640, 500:850]
    cropped_rotated_path = '../test_urbana/crop_rotated_image.jpg'
    cv2.imwrite(cropped_rotated_path, cropped_rotated)
    return cropped_rotated_path

def register_images(image1_path, image2_path, threshold, matcher_type, scale_percent=100):
    start_time = time.time()
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img1 = cv2.circle(img1, (789, 111), 10, (0,0,255), 5)
    print("size of img1, ", img1.shape)
    cv2.imwrite('../test_urbana/before_crop_rotate.jpg', img1)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    # change the depth of the bits
    if img1.dtype != np.uint8:
        # check max val
        img1 = np.uint8(img1 / 256)
    if img2.dtype != np.uint8:
        img2 = np.uint8(img2 / 256)
    # reduce resolution
    width = int(img1.shape[1] * scale_percent / 100)
    height = int(img1.shape[0] * scale_percent / 100)
    dim = (width, height)
    img1 = cv2.resize(img1, dim, interpolation=cv2.INTER_AREA)
    # img2 = cv2.resize(img2, dim, interpolation=cv2.INTER_AREA)
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
    print("Ref and sensed dimentions")
    h, w = img1.shape
    # least squared => linear regression
    # sensed = np.float32([[0,0], [1,1], [1,0]])
    # ref = np.float32([[10,20], [11,21], [11,20]])
    print(ref)
    print(sensed)
    M = cv2.getAffineTransform(sensed, ref)
    registered_img = cv2.warpAffine(img2, M, (w, h))
    # registered_img = cv2.warpPerspective(img2, H, (w, h))
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration:.2f} seconds")
    return registered_img, M

# registered_img = register_images('path_to_image1.tif', 'path_to_image2.tif', 0.75, "flann", scale_percent=50)
img1_path = '../test_urbana/20231006_154931_98_24b5_3B_Visual_clip.tif'
img1_geo_json_path = '../test_urbana/20231006_154931_98_24b5_metadata.json'
img2_path = crop_and_rotate_image(img1_path)
registered_img, M = register_images(img1_path, img2_path, 0.75, "bf", scale_percent=50)
if registered_img is not None:
    print("M: ", M)
    cv2.imwrite('../test_urbana/registered_image_lowres_cropped.jpg', registered_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    overlay_images('../test_urbana/before_crop_rotate.jpg', '../test_urbana/registered_image_lowres_cropped.jpg', 0.5)
    # predicted_coors = transform_coordinates(img1_geo_json_path, H)
    point_homogeneous = np.array([0, 0, 1])
        # Apply the transformation matrix
    point_transformed_homogeneous = np.dot(M, point_homogeneous)
    print(point_transformed_homogeneous)
    # for predicted_coor in predicted_coors:
    #     print(predicted_coor)
