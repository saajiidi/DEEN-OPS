import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_modules.pathao_client import PathaoClient
from app_modules.ui_config import PATHAO_CONFIG

# For standalone script usage, manual secrets load if needed
if not PATHAO_CONFIG or PATHAO_CONFIG.get("username") == "test@pathao.com":
    try:
        import toml
        secrets = toml.load(".streamlit/secrets.toml")
        if "pathao" in secrets:
            PATHAO_CONFIG = secrets["pathao"]
            print("Loaded Pathao config from secrets.toml")
    except:
        pass

def update_pathao_data():
    client = PathaoClient(**PATHAO_CONFIG)
    print("Fetching cities...")
    cities = client.get_cities()
    
    full_map = {}
    
    for city in cities:
        c_id = city['city_id']
        c_name = city['city_name']
        print(f"Fetching zones for {c_name} (ID: {c_id})...")
        zones = client.get_zones(c_id)
        
        full_map[c_name] = {
            "city_id": c_id,
            "zones": {}
        }
        
        for zone in zones:
            z_id = zone['zone_id']
            z_name = zone['zone_name']
            print(f"  Fetching areas for {z_name} (ID: {z_id})...")
            areas = client.get_areas(z_id)
            
            full_map[c_name]["zones"][z_name] = {
                "zone_id": z_id,
                "areas": areas
            }
            
    os.makedirs("resources", exist_ok=True)
    with open("resources/pathao_map.json", "w") as f:
        json.dump(full_map, f, indent=4)
        
    print("Pathao data update complete! Saved to resources/pathao_map.json")

if __name__ == "__main__":
    update_pathao_data()
