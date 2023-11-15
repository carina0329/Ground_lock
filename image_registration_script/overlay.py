import cv2

def overlay_images(original_image_path, registered_image_path, alpha):
    # Load the images
    original_image = cv2.imread(original_image_path)
    registered_image = cv2.imread(registered_image_path)
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
    cv2.imwrite(f'../test_urbana/overlayed_rotate_lowres.jpg', blended_image)

if __name__ == '__main__':
    overlay_images("../test_urbana/image_to_be_registered.jpg", "../test_urbana/registered_image_lowres_cropped.jpg", 0.5)