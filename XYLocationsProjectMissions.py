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

# Function to get the most recent missions in an organization
def get_most_recent_missions_in_org(api_token, org_id, feature_layer):
    print(f"Processing most recent missions for organization ID {org_id}...")
    projects = get_all_projects(api_token, org_id)
    
    new_features = []
    
    for project in projects:
        project_id = project['id']
        project_name = project['name']
        missions = get_all_missions(api_token, project_id)
        mission_count = len(missions)  # Count the number of missions for this project
        
        # Find the most recent mission
        if missions:
            most_recent_mission = max(missions, key=lambda m: parse(m.get('endTime', m['created'])))
            latitude, longitude = get_first_media_location(api_token, most_recent_mission['id'])
            mission_url = f"https://sitescan.arcgis.com/projects/{project_id}/missions/{most_recent_mission['id']}"
            
            # Parse end time to ensure it's in UTC
            end_time_utc = parse(most_recent_mission.get('endTime', most_recent_mission['created'])).astimezone(timezone.utc)
            
            feature = {
                'attributes': {
                    'OrgID': org_id,  # Add OrgID here
                    'project_id': project_id,
                    'project_name': project_name,
                    'mission_id': most_recent_mission['id'],
                    'mission_name': most_recent_mission['name'],
                    'end_time': int(end_time_utc.timestamp() * 1000),  # Ensure the time is in milliseconds since epoch
                    'latitude': latitude,
                    'longitude': longitude,
                    'mission_url': mission_url,
                    'ProjectCount': mission_count  # Added mission count here
                },
                'geometry': {
                    'x': longitude,
                    'y': latitude,
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
        print(f"Added {len(new_features)} new features.")

# Example usage
api_token = ''  # Replace with your actual API token
org_id = ''  # Replace with your actual organization ID
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
        get_most_recent_missions_in_org(api_token, org_id, feature_layer)
