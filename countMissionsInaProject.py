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

# Function to get the first media location
def get_first_media_location(api_token, mission_id):
    print(f"Retrieving media location for mission ID {mission_id}...")
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    media_url = f'https://sitescan-api.arcgis.com/api/v2/missions/{mission_id}/media'
    response = requests.get(media_url, headers=headers)
    response.raise_for_status()
    media = response.json()
    if media:
        first_media = media[0]
        location = first_media.get('location', {})
        coordinates = location.get('coordinates', [])
        if coordinates:
            print(f"Retrieved location for mission ID {mission_id}.")
            return coordinates[1], coordinates[0]  # latitude, longitude
    print(f"No location available for mission ID {mission_id}.")
    return None, None

# Function to check and add 'mission_count' field if it doesn't exist
def add_mission_count_field_if_not_exists(feature_layer):
    fields = feature_layer.properties.fields
    if not any(field['name'] == 'mission_count' for field in fields):
        field_def = {
            "name": "mission_count",
            "type": "esriFieldTypeInteger",
            "alias": "Mission Count"
        }
        feature_layer.manager.add_to_definition({"fields": [field_def]})
        print("Added 'mission_count' field to the feature layer.")
    else:
        print("'mission_count' field already exists in the feature layer.")

# Function to get the most recent missions in a specific project
def get_most_recent_missions_in_project(api_token, project_id, project_name, feature_layer):
    print(f"Processing most recent missions for project ID {project_id}...")
    new_features = []

    missions = get_all_missions(api_token, project_id)
    
    # List and count all missions
    print(f"Total number of missions in project '{project_name}': {len(missions)}")
    mission_count = 0
    for mission in missions:
        mission_count += 1
        latitude, longitude = get_first_media_location(api_token, mission['id'])
        mission_url = f"https://sitescan.arcgis.com/projects/{project_id}/missions/{mission['id']}"
        
        # Parse end time to ensure it's in UTC
        end_time_utc = parse(mission.get('endTime', mission['created'])).astimezone(timezone.utc)
        
        feature = {
            'attributes': {
                'project_id': project_id,
                'project_name': project_name,
                'mission_id': mission['id'],
                'mission_name': mission['name'],
                'end_time': int(end_time_utc.timestamp() * 1000),  # Ensure the time is in milliseconds since epoch
                'latitude': latitude,
                'longitude': longitude,
                'mission_url': mission_url,
                'mission_count': mission_count  # Set the mission count incrementally
            },
            'geometry': {
                'x': longitude,
                'y': latitude,
                'spatialReference': {'wkid': 4326}
            }
        }
        new_features.append(feature)
            
    if new_features:
        # Delete existing features for this project
        feature_layer.delete_features(where=f"project_id = '{project_id}'")
        print(f"Deleted existing features for project ID {project_id}.")
        
        # Add new features
        feature_layer.edit_features(adds=new_features)
        print(f"Added {len(new_features)} new features.")

# Example usage
api_token = ''  # Replace with your actual API token
project_id = ''  # Replace with your specific project ID
project_name = ''  # Replace with your specific project name
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
        add_mission_count_field_if_not_exists(feature_layer)
        get_most_recent_missions_in_project(api_token, project_id, project_name, feature_layer)