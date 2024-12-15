import os
import yaml
import requests

class OpenNebulaManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.clusters = self.load_clusters()

    def load_clusters(self):
        clusters = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    config = yaml.safe_load(f)
                    cluster_name = os.path.splitext(filename)[0]
                    clusters[cluster_name] = config
        return clusters

    def get_cluster_config(self, cluster_name):
        return self.clusters.get(cluster_name)

    def create_vm(self, cluster_name, profile):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        token = config['opennebula_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Create VM payload from profile
        payload = {
            "vm": {
                "name": profile['hostname_pattern'].format(index=1),
                "template": profile['template_id'],
                "cpu": profile['cpu'],
                "memory": profile['memory'],
                "disks": profile['disks'],
                "networks": profile['networks']
            }
        }

        response = requests.post(f"{api_url}/vm", json=payload, headers=headers)
        if response.status_code == 201:
            print(f"VM created successfully in cluster {cluster_name}.")
        else:
            print(f"Failed to create VM in cluster {cluster_name}: {response.text}")

    def delete_vm(self, cluster_name, vm_id):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        token = config['opennebula_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.delete(f"{api_url}/vm/{vm_id}", headers=headers)
        if response.status_code == 200:
            print(f"VM {vm_id} deleted successfully from cluster {cluster_name}.")
        else:
            print(f"Failed to delete VM {vm_id} from cluster {cluster_name}: {response.text}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        token = config['opennebula_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(f"{api_url}/vm", headers=headers)
        if response.status_code == 200:
            vms = response.json().get('vms', [])
            for vm in vms:
                print(f"VM ID: {vm['id']}, Name: {vm['name']}, Status: {vm['status']}")
        else:
            print(f"Failed to list VMs in cluster {cluster_name}: {response.text}")

    def modify_vm(self, cluster_name, vm_id, profile):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        token = config['opennebula_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Fetch the existing VM configuration
        response = requests.get(f"{api_url}/vm/{vm_id}", headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch VM {vm_id} from cluster {cluster_name}: {response.text}")
            return

        vm_config = response.json()

        # Apply modifications from the profile to the VM configuration
        vm_config['vm']['cpu'] = profile['cpu']
        vm_config['vm']['memory'] = profile['memory']
        vm_config['vm']['disks'] = profile['disks']
        vm_config['vm']['networks'] = profile['networks']

        # Update the VM with the modified configuration
        response = requests.put(f"{api_url}/vm/{vm_id}", json=vm_config, headers=headers)
        if response.status_code == 200:
            print(f"VM {vm_id} modified successfully in cluster {cluster_name}.")
        else:
            print(f"Failed to modify VM {vm_id} in cluster {cluster_name}: {response.text}")
