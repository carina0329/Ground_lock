import cv2
import numpy as np
import matplotlib.pyplot as plt
import time

def register_images(image1_path, image2_path, threshold, matcher_type):
    start_time = time.time()
    # Read the images, convert them to grayscale
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    # img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE) 
    (h, w) = img1.shape[:2]
    center = (w / 2, h / 2)
    # Set the angle of rotation
    angle = 45 
    # Get the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Perform the rotation
    rotated = cv2.warpAffine(img1, M, (w, h))
    cv2.imwrite('../test_urbana/img1.jpg', img1)
    cv2.imwrite('../test_urbana/img2.jpg', rotated)
    # sift feature detector
    sift = cv2.SIFT_create()
    # kp is key point, des is descriptor
    kp1, des1 = sift.detectAndCompute(img1, None)
    # print("descriptor vector", des1[0])
    kp2, des2 = sift.detectAndCompute(rotated, None)
    matcher = None
    if matcher_type == "bf":
    # brute force BFMatcher with default params
        matcher = cv2.BFMatcher()
    elif matcher_type == "flann":
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    matches = matcher.knnMatch(des1,des2,k=2)
    print("number of matches detected", len(matches))
    # Apply Lowe's ratio test
    good_matches = []
    for m,n in matches:
        # print(m)
        if m.distance < threshold*n.distance:
            good_matches.append(m)
    print("number of good matches detected", len(good_matches))
    # matchedVis = cv2.drawMatches(img1, kp1, img2, kp2, matches[:15], 5)
    # cv2.imshow("Matched Keypoints", matchedVis)
    # Extract location of good matches
     # look into indices
    ref = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    sensed = np.float32([kp2[m.trainIdx].pt for m in good_matches])

    # compute spatial relationship, use random sample consensus
    H, status = cv2.findHomography(sensed, ref, cv2.RANSAC)
    # register the first image
    h, w = img1.shape
    print(H)
    registered_img = cv2.warpPerspective(rotated, H, (w, h))
    end_time = time.time()
    # Calculate and print the duration
    duration = end_time - start_time
    print(f"Execution time: {duration:.2f} seconds")
    return registered_img

# Example usage
# brute force feature matcher
registered_img = register_images('../test_urbana/20231006_154931_98_24b5_3B_Visual_clip.tif', '../test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif', 0.75, "bf")
# registered_img = register_images('test_urbana/20231006_154931_98_24b5_3B_Visual_clip.tif', 'test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif', 0.75, "bf")
# # flann feature matcher
# registered_img = register_images('test_urbana/20231006_154931_98_24b5_3B_Visual_clip.tif', 'test_urbana/20231006_154454_21_2449_3B_Visual_clip.tif', 0.75, "flann")
cv2.imwrite('../test_urbana/registered_image.jpg', registered_img)