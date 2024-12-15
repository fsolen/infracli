import os
import yaml
import requests

class HarvesterManager:
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

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Create VM payload from profile
        payload = {
            "metadata": {
                "name": profile['hostname_pattern'].format(index=1),
                "namespace": "default"
            },
            "spec": {
                "template": {
                    "spec": {
                        "domain": {
                            "cpu": {
                                "cores": profile['cpu']
                            },
                            "devices": {
                                "disks": [
                                    {
                                        "disk": {
                                            "bus": "virtio"
                                        },
                                        "name": disk['name'],
                                        "size": f"{disk['size_gb']}Gi"
                                    } for disk in profile['disks']
                                ]
                            },
                            "resources": {
                                "requests": {
                                    "memory": f"{profile['memory']}Mi"
                                }
                            }
                        },
                        "networks": [
                            {
                                "name": "default",
                                "pod": {}
                            }
                        ]
                    }
                }
            }
        }

        response = requests.post(f"{api_url}/v1/kubevirt.io.virtualmachines", json=payload, headers=headers)
        if response.status_code == 201:
            print(f"VM created successfully in cluster {cluster_name}.")
        else:
            print(f"Failed to create VM in cluster {cluster_name}: {response.text}")

    def delete_vm(self, cluster_name, vm_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.delete(f"{api_url}/v1/kubevirt.io.virtualmachines/default/{vm_name}", headers=headers)
        if response.status_code == 200:
            print(f"VM {vm_name} deleted successfully from cluster {cluster_name}.")
        else:
            print(f"Failed to delete VM {vm_name} from cluster {cluster_name}: {response.text}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(f"{api_url}/v1/kubevirt.io.virtualmachines", headers=headers)
        if response.status_code == 200:
            vms = response.json().get('items', [])
            for vm in vms:
                print(f"VM Name: {vm['metadata']['name']}, Status: {vm['status']['phase']}")
        else:
            print(f"Failed to list VMs in cluster {cluster_name}: {response.text}")

    def modify_vm(self, cluster_name, vm_name, modifications):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Fetch the existing VM configuration
        response = requests.get(f"{api_url}/v1/kubevirt.io.virtualmachines/default/{vm_name}", headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch VM {vm_name} from cluster {cluster_name}: {response.text}")
            return

        vm_config = response.json()

        # Apply modifications to the VM configuration
        for key, value in modifications.items():
            if key in vm_config['spec']['template']['spec']['domain']:
                vm_config['spec']['template']['spec']['domain'][key] = value
            elif key in vm_config['spec']['template']['spec']['domain']['devices']:
                vm_config['spec']['template']['spec']['domain']['devices'][key] = value
            else:
                print(f"Modification key {key} not found in VM configuration.")
                return

        # Update the VM with the modified configuration
        response = requests.put(f"{api_url}/v1/kubevirt.io.virtualmachines/default/{vm_name}", json=vm_config, headers=headers)
        if response.status_code == 200:
            print(f"VM {vm_name} modified successfully in cluster {cluster_name}.")
        else:
            print(f"Failed to modify VM {vm_name} in cluster {cluster_name}: {response.text}")
