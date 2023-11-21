import cv2
import numpy as np
import time
import json

def extract_coordinates(geojson_file_path):
    with open(geojson_file_path, 'r') as file:
        geojson_data = json.load(file)
    all_coordinates = []
    # Check if the file contains a Feature or a FeatureCollection
    if geojson_data['type'] == 'Feature':
        coordinates = geojson_data['geometry']['coordinates']
        all_coordinates.append(coordinates)
    elif geojson_data['type'] == 'FeatureCollection':
        for feature in geojson_data['features']:
            coordinates = feature['geometry']['coordinates']
            all_coordinates.append(coordinates)
    else:
        print("The GeoJSON file does not contain Feature or FeatureCollection types.")
    return all_coordinates

def transform_coordinates(geojson_file_path, transformed_corners, original_dim):
    all_coordinates = extract_coordinates(geojson_file_path)
    # calculate the percentage
    w, h = original_dim
    
    
# this function is designated to verify the correctness of image registration
def crop_and_rotate_image(image_path, cropped_rotated_path, col_crop_tuple, row_crop_tuple):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    (h, w) = img.shape[:2]
    center = (w / 2, h / 2)
    # Set the angle of rotation
    angle = 45 
    # Get the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Perform the rotation
    rotated = cv2.warpAffine(img, M, (w, h))
    # cropped_rotated = rotated[320:640, 500:850]
    cropped_rotated = rotated[row_crop_tuple[0]:row_crop_tuple[1], col_crop_tuple[0]:col_crop_tuple[1]]
    # cropped_rotated_path = '../test_urbana/crop_rotated_image.jpg'
    cv2.imwrite(cropped_rotated_path, cropped_rotated)

# this function is to perform the actual image registration process
def register_images(image1_path, image2_path, threshold, matcher_type, scale_percent=100):
    start_time = time.time()
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    # change the depth of the bits
    if img1.dtype != np.uint8:
        # check max val
        img1 = np.uint8(img1 / 256)
    if img2.dtype != np.uint8:
        img2 = np.uint8(img2 / 256)
    # reduce resolution
    width1 = int(img1.shape[1] * scale_percent / 100)
    height1 = int(img1.shape[0] * scale_percent / 100)
    width2 = int(img2.shape[1] * scale_percent / 100)
    height2 = int(img2.shape[0] * scale_percent / 100)
    dim1 = (width1, height1)
    dim2 = (width2, height2)
    img1 = cv2.resize(img1, dim1, interpolation=cv2.INTER_AREA)
    img2 = cv2.resize(img2, dim2, interpolation=cv2.INTER_AREA)
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
    else:
        return -1
    matches = matcher.knnMatch(des1, des2, k=2)
    good_matches = [m for m, n in matches if m.distance < threshold * n.distance]
    print("number of good matches detected: ", len(good_matches))
    ref = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    sensed = np.float32([kp2[m.trainIdx].pt for m in good_matches])
    H, status = cv2.findHomography(sensed, ref, cv2.RANSAC)
    h, w = img1.shape
    h2, w2 = img2.shape
    registered_img = cv2.warpPerspective(img2, H, (w, h))
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration:.2f} seconds")
    matrix_original = np.array([
        [0, 0, 1],# Bottom-left corner
        [w2, 0, 1],# Bottom-right corner
        [0, h2, 1],# Top-left corner
        [w2, h2, 1]# Top-right corner
    ])
    print(matrix_original)
    transformed_corners = np.matmul(H, matrix_original.T)
    # Normalize to convert from homogeneous to Cartesian coordinates
    transformed_corners /= transformed_corners[2, :]
    # Extract the Cartesian coordinates
    transformed_corners = transformed_corners[:2, :].T
    print(transformed_corners)
    return H, registered_img, transformed_corners

def overlay_images(original_image_path, registered_image, blended_image_path, alpha):
    # Load the images
    original_image = cv2.imread(original_image_path)
    # registered_image = cv2.imread(registered_image_path)
    # resize
    registered_image = cv2.resize(registered_image, (original_image.shape[1], original_image.shape[0]))
    # Convert to color if they're grayscale
    if len(original_image.shape) == 2:
        original_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
    if len(registered_image.shape) == 2:
        registered_image = cv2.cvtColor(registered_image, cv2.COLOR_GRAY2BGR)
    # Set transparency: 0.0 is fully transparent, 1.0 is fully opaque
    # Blend the images
    blended_image = cv2.addWeighted(original_image, 1 - alpha, registered_image, alpha, 0)
    cv2.imwrite(blended_image_path, blended_image)