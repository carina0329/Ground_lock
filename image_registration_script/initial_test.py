from image_registration_helper import *
# iou - best match is 1
# basemap test
# WSG 3857: How to query basemap
img1_path = '../test_urbana/20231006_154931_98_24b5_3B_Visual_clip.tif'
img1_name = img1_path.split('.')[:-1][-1]
img1_geo_json_path = '../test_urbana/20231006_154931_98_24b5_metadata.json'
img2_path = f'..{img1_name}_cropped_rotated.jpg'
print(img2_path)
crop_and_rotate_image(img1_path, img2_path, (320, 640), (500, 850))
H, registered_img, transformed_corners = register_images(img1_path, img2_path, 0.75, "bf", scale_percent=50)
print(H)
if registered_img is not None:
    cv2.imwrite('../test_urbana/registered_image_lowres_cropped.jpg', registered_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    overlay_images(img1_path, registered_img, img2_path, 0.5)