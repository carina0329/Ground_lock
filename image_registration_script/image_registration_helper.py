import cv2
import numpy as np
import time
import json
from shapely.geometry import Polygon
from sklearn.linear_model import LinearRegression
from rotate_image import *
# sift similarity
# linear regression quality returned by Ransac
# normalize basemap and do pixel by pixel
# linear regression between 2 sets => y - Hx
# Function to evaluate the quality of homography using linear regression
def evaluate_homography_quality(transformed_pts, dst_pts):
    # transformed_pts = cv2.perspectiveTransform(np.array([src_pts]), H)[0]
    model = LinearRegression().fit(transformed_pts, dst_pts)
    return model.score(transformed_pts, dst_pts)

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
    return all_coordinates[0][0]

def extract_coordinates_basemap(geojson_file_path):
    try:
        with open(geojson_file_path, 'r') as file:
            data = json.load(file)
            bbox = data.get('bbox', None)
            if bbox:
                return bbox
            else:
                raise ValueError("Bounding box not found in the provided GeoJSON file.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# [min_lon, min_lat, max_lon, max_lat]
def transform_coordinates(geojson_file_path, transformed_corners, original_dim):
    min_lon, min_lat, max_lon, max_lat = extract_coordinates_basemap(geojson_file_path)
    print("bbox", min_lon, " " ,min_lat, " ", max_lon,  " ", max_lat)
    # calculate the percentage
    w, h = original_dim
    geo_coords = []
    for corner in transformed_corners:
        x_percent = corner[0] / w
        y_percent = corner[1] / h
        lon = min_lon + x_percent * (max_lon - min_lon)
        lat = min_lat + y_percent * (max_lat - min_lat)
        geo_coords.append((lon, lat))
    return geo_coords

def compute_iou(geo_coords1, geo_coords2):
    polygon1 = Polygon(geo_coords1)
    print(polygon1)
    polygon2 = Polygon(geo_coords2)
    print(polygon2)
    intersection = polygon1.intersection(polygon2).area
    union = polygon1.union(polygon2).area
    return intersection / union if union != 0 else 0
    
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
    img2 = cv2.imread(image2_path)
    img2_rotated, angle = rotate_image(img2)
    img2_rotated = cv2.convertScaleAbs(img2_rotated)
    img2_rotated = cv2.cvtColor(img2_rotated, cv2.COLOR_BGR2GRAY)
    # change the depth of the bits, 8 bits per pixel (Visual)
    if img1.dtype != np.uint8:
        # check max val
        img1 = np.uint8(img1 / 256)
    if img2_rotated.dtype != np.uint8:
        img2_rotated = np.uint8(img2_rotated / 256)
    # reduce resolution
    width1 = int(img1.shape[1] * scale_percent / 100)
    height1 = int(img1.shape[0] * scale_percent / 100)
    width2 = int(img2_rotated.shape[1] * scale_percent / 100)
    height2 = int(img2_rotated.shape[0] * scale_percent / 100)
    dim1 = (width1, height1)
    dim2 = (width2, height2)
    img1 = cv2.resize(img1, dim1, interpolation=cv2.INTER_AREA)
    img2 = cv2.resize(img2_rotated, dim2, interpolation=cv2.INTER_AREA)
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
    all_matches = []
    for m, n in matches:
        all_matches.append(m)
    print("number of matches found: ", len(matches))
    good_matches = [m for m, n in matches if m.distance < threshold * n.distance]
    # good_matches_img = cv2.drawMatches(img1, kp1, img2, kp2, all_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    # cv2.imshow("Good Matches", good_matches_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    print("number of good matches detected: ", len(good_matches))
    if len(good_matches) < 20:
        print("Not enough matches to find a homography.")
        return None, None, None, (0, 0)
    ref = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    sensed = np.float32([kp2[m.trainIdx].pt for m in good_matches])
    print(sensed)
    H, status = cv2.findHomography(sensed, ref, cv2.RANSAC)
    transformed_ref = []
    for ref_point in ref:
        single_ref_point_x,  single_ref_point_y = ref_point
        single_ref_point = np.array([
            [single_ref_point_x, single_ref_point_y, 1]
        ])
        transformed_single_ref_point = np.matmul(H, single_ref_point.T)
        transformed_single_ref_point /= transformed_single_ref_point[2, :]
        transformed_single_ref_point = transformed_single_ref_point[:2, :].T
        transformed_ref.extend(transformed_single_ref_point)
    transformed_ref = np.float32(transformed_ref)
    # print(np.float32(transformed_ref))
    diff = transformed_ref - ref
    print("Diff is: ", diff)
    print("H is: ", H)
    print("Status is: ", status)
    if H is None:
        print("Matches fail to form a valid homography.")
        return None, None, None, (0, 0)
    h, w = img1.shape
    h2, w2 = img2.shape
    registered_img = cv2.warpPerspective(img2, H, (w, h))
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration:.2f} seconds")
    matrix_original = np.array([
        [0, 0, 1],# Bottom-left corner
        [w2, 0, 1],# Bottom-right corner
        [w2, h2, 1],# Top-right corner
        [0, h2, 1]# Top-left corner
    ])
    print(matrix_original)
    print("-----------------------------------------")
    # print(evaluate_homography_quality(registered_img, img2))
    transformed_corners = np.matmul(H, matrix_original.T)
    # Normalize to convert from homogeneous to Cartesian coordinates
    transformed_corners /= transformed_corners[2, :]
    # Extract the Cartesian coordinates
    transformed_corners = transformed_corners[:2, :].T
    print(transformed_corners)
    return H, registered_img, transformed_corners, (w,h)

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
    blended_image = cv2.addWeighted(original_image, 1 - alpha, registered_image, alpha, 0)
    cv2.imwrite(blended_image_path, blended_image)