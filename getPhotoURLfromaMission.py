# This gets the photo URLs from a mission

import requests
from datetime import datetime, timezone
from dateutil.parser import parse
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import getpass  # To securely get password input

# Initialize GIS with username and password
print("Please enter your ArcGIS Online credentials:")
username = input("Username: ")
password = getpass.getpass("Password: ")
gis = GIS("https://www.arcgis.com", username, password)
print("Connected to ArcGIS Online using user credentials.")

# Function to retrieve all projects
def get_all_projects(api_token, org_id):
    print("Retrieving all projects from SiteScan...")
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    projects_url = f'https://sitescan-api.arcgis.com/api/v2/organizations/{org_id}/projects'
    response = requests.get(projects_url, headers=headers)
    response.raise_for_status()
    projects = response.json()
    print(f"Retrieved {len(projects)} projects.")
    return projects

# Function to retrieve all missions for a given project
def get_all_missions(api_token, project_id):
    print(f"Retrieving all missions for project ID {project_id}...")
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    missions_url = f'https://sitescan-api.arcgis.com/api/v2/projects/{project_id}/missions'
    response = requests.get(missions_url, headers=headers)
    response.raise_for_status()
    missions = response.json()
    return missions

# Function to get all media locations and URLs for a mission
def get_all_media_locations_and_urls(api_token, mission_id):
    print(f"Retrieving all media locations and URLs for mission ID {mission_id}...")
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    media_url = f'https://sitescan-api.arcgis.com/api/v2/missions/{mission_id}/media'
    response = requests.get(media_url, headers=headers)
    response.raise_for_status()
    media = response.json()
    media_list = []
    if media:
        for media_item in media:
            location = media_item.get('location', {})
            coordinates = location.get('coordinates', [])
            photo_url = media_item.get('url', '')
            if coordinates and photo_url:
                media_list.append({
                    'latitude': coordinates[1],
                    'longitude': coordinates[0],
                    'photo_url': photo_url
                })
        print(f"Retrieved {len(media_list)} media locations and URLs for mission ID {mission_id}.")
    else:
        print(f"No media available for mission ID {mission_id}.")
    return media_list

# Function to get all media from a specific mission and update the feature layer
def update_feature_layer_with_mission_media(api_token, project_id, mission_id, feature_layer):
    media_list = get_all_media_locations_and_urls(api_token, mission_id)
    new_features = []
    
    # Retrieve project name and mission name
    projects = get_all_projects(api_token, org_id)
    project_name = next((project['name'] for project in projects if project['id'] == project_id), None)
    missions = get_all_missions(api_token, project_id)
    mission_name = next((mission['name'] for mission in missions if mission['id'] == mission_id), None)
    
    # Incremental photo count
    photo_count = 0
    
    for media_item in media_list:
        photo_count += 1
        feature = {
            'attributes': {
                'project_id': project_id,
                'project_name': project_name,
                'mission_id': mission_id,
                'mission_name': mission_name,
                'photo_url': media_item['photo_url'],
                'photo_count': photo_count  # Incremental photo count
            },
            'geometry': {
                'x': media_item['longitude'],
                'y': media_item['latitude'],
                'spatialReference': {'wkid': 4326}
            }
        }
        new_features.append(feature)
    
    if new_features:
        # Delete existing features
        feature_layer.delete_features(where="1=1")
        print("Deleted existing features.")
        
        # Add new features
        feature_layer.edit_features(adds=new_features)
        print(f"Added {len(new_features)} new features with media URLs and photo count.")

# Example usage
api_token = ''  # Replace with your actual API token
org_id = ''  # Replace with your actual organization ID
project_id = ''  # Replace with your actual project ID
mission_id = ''  # Replace with your actual mission ID
item_id = ""  # Replace with your actual feature layer item ID

# Debug information
print(f"Using item ID: {item_id}")

feature_layer_item = gis.content.get(item_id)
if feature_layer_item is None:
    print(f"Feature layer item with ID {item_id} not found.")
else:
    print(f"Feature layer item found: {feature_layer_item.title}")
    if not feature_layer_item.layers:
        print(f"No layers found in item with ID {item_id}.")
    else:
        feature_layer = feature_layer_item.layers[0]
        update_feature_layer_with_mission_media(api_token, project_id, mission_id, feature_layer)
