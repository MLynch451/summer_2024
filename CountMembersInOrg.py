import requests
from arcgis.gis import GIS
from arcgis.features import FeatureLayer, Feature
import getpass

# Initialize GIS with username and password
print("Please enter your ArcGIS Online credentials:")
username = input("Username: ")
password = getpass.getpass("Password: ")
gis = GIS("https://www.arcgis.com", username, password)
print("Connected to ArcGIS Online using user credentials.")

# Function to retrieve member counts and organization name from Site Scan API organization
def get_org_info(api_token, org_id):
    print("Retrieving organization info from SiteScan...")
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    org_url = f'https://sitescan-api.arcgis.com/api/v2/organizations/{org_id}'
    members_url = f'https://sitescan-api.arcgis.com/api/v2/organizations/{org_id}/members'

    # Retrieve organization info
    org_response = requests.get(org_url, headers=headers)
    org_response.raise_for_status()
    org_info = org_response.json()
    org_name = org_info['name']

    # Retrieve member count
    members_response = requests.get(members_url, headers=headers)
    members_response.raise_for_status()
    members = members_response.json()
    member_count = len(members)

    print(f"Retrieved organization info: name={org_name}, member_count={member_count}.")
    return org_name, member_count

# Function to add a field if it doesn't exist
def add_field_if_not_exists(feature_layer, field_name, field_type="esriFieldTypeString"):
    fields = feature_layer.properties.fields
    field_names = [field['name'] for field in fields]
    if field_name not in field_names:
        new_field = {
            "name": field_name,
            "type": field_type,
            "alias": field_name,
            "nullable": True
        }
        feature_layer.manager.add_to_definition({"fields": [new_field]})
        print(f"Field '{field_name}' added to the feature layer.")
    else:
        print(f"Field '{field_name}' already exists in the feature layer.")

# Function to update the AGOL feature class with organization info
def update_agol_feature_class(api_token, org_id, feature_layer):
    print(f"Updating AGOL feature class for organization ID {org_id}...")
    org_name, member_count = get_org_info(api_token, org_id)
    
    # Add the member_count and org_name fields if they don't exist
    add_field_if_not_exists(feature_layer, "member_count", field_type="esriFieldTypeInteger")
    add_field_if_not_exists(feature_layer, "org_name")
    
    # Create a new feature with the organization info
    feature = {
        'attributes': {
            'org_id': org_id,
            'org_name': org_name,
            'member_count': member_count
        }
    }
    
    # Delete existing features
    feature_layer.delete_features(where="1=1")
    print("Deleted existing features.")
    
    # Add the new feature
    feature_layer.edit_features(adds=[feature])
    print("Added new feature with organization info.")

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
        update_agol_feature_class(api_token, org_id, feature_layer)
