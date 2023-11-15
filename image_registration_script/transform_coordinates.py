import json
import numpy as np

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
# coordinates_list = extract_coordinates('../test_urbana/20231006_154454_21_2449_metadata.json')

def transform_coordinates(geojson_file_path, H):
    coordinates = extract_coordinates(geojson_file_path)[0][0]
    print("coor", coordinates)
    transformed_coordinates = []
    for point in coordinates:
        # Convert to homogeneous coordinates
        point_homogeneous = np.array([0, 0, 1])
        # Apply the transformation matrix
        point_transformed_homogeneous = np.dot(H, point_homogeneous)
        # Convert back to 2D coordinates
        point_transformed = point_transformed_homogeneous[:2] / point_transformed_homogeneous[2]
        transformed_coordinates.append(point_transformed.tolist())
    return transformed_coordinates

