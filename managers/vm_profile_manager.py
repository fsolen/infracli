import os
import yaml

def load_profiles(profiles_path):
    profiles = {}
    for filename in os.listdir(profiles_path):
        if filename.endswith(".yaml"):
            try:
                with open(os.path.join(profiles_path, filename), 'r') as f:
                    profile = yaml.safe_load(f)
                    profile_name = os.path.splitext(filename)[0]
                    profiles[profile_name] = profile
            except Exception as e:
                print(f"Error loading profile {filename}: {str(e)}")
    return profiles
