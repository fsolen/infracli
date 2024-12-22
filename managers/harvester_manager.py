import os
import yaml
from .phpipam_manager import PhpIpamManager

class HarvesterManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.clusters = self.load_clusters()
        self.phpipam_manager = PhpIpamManager(config_path)

    def load_clusters(self):
        clusters = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(self.config_path, filename), 'r') as f:
                        cluster = yaml.safe_load(f)
                        cluster_name = os.path.splitext(filename)[0]
                        clusters[cluster_name] = cluster
                except Exception as e:
                    print(f"Error loading cluster {filename}: {str(e)}")
        return clusters

    def get_cluster_config(self, cluster_name):
        return self.clusters.get(cluster_name)

    def allocate_ip(self, vm_profile):
        vlan_name = vm_profile.get('vlan')
        if vlan_name:
            try:
                network_info = self.phpipam_manager.get_network_info(vlan_name)
                return network_info
            except Exception as e:
                print(f"Error allocating IP for VLAN {vlan_name}: {str(e)}")
                raise
        else:
            raise ValueError("VLAN not specified in vm_profile")

    def create_vm(self, cluster_name, profile_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        profile = self.profiles.get(profile_name)
        if not profile:
            print(f"Profile {profile_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        try:
            network_info = self.allocate_ip(profile)
        except Exception as e:
            print(f"Error allocating IP: {str(e)}")
            return

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
                        ],
                        "interfaces": [
                            {
                                "name": "default",
                                "ipAddress": network_info['ip_address'],
                                "subnetMask": network_info['subnet_mask'],
                                "gateway": network_info['gateway'],
                                "dnsServers": network_info['dns_servers']
                            }
                        ]
                    }
                }
            }
        }

        response = requests.post(f"{api_url}/v1/vms", headers=headers, json=payload)
        if response.status_code == 201:
            print(f"VM {profile['hostname_pattern'].format(index=1)} created in cluster {cluster_name}.")
        else:
            print(f"Failed to create VM in cluster {cluster_name}: {response.text}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(f"{api_url}/v1/vms", headers=headers)
        if response.status_code == 200:
            vms = response.json().get('items', [])
            for vm in vms:
                print(f"VM Name: {vm['metadata']['name']}, Namespace: {vm['metadata']['namespace']}, State: {vm['status']['phase']}")
        else:
            print(f"Failed to list VMs in cluster {cluster_name}: {response.text}")

    def modify_vm(self, cluster_name, vm_name, profile):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['harvester_api_url']
        token = config['harvester_api_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Fetch the existing VM configuration
        response = requests.get(f"{api_url}/v1/vms/{vm_name}", headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch VM {vm_name} in cluster {cluster_name}: {response.text}")
            return

        vm_config = response.json()

        # Modify the VM configuration based on the profile
        vm_config['spec']['template']['spec']['domain']['cpu']['cores'] = profile['cpu']
        vm_config['spec']['template']['spec']['domain']['resources']['requests']['memory'] = f"{profile['memory']}Mi"
        vm_config['spec']['template']['spec']['domain']['devices']['disks'] = [
            {
                "disk": {
                    "bus": "virtio"
                },
                "name": disk['name'],
                "size": f"{disk['size_gb']}Gi"
            } for disk in profile['disks']
        ]

        response = requests.put(f"{api_url}/v1/vms/{vm_name}", headers=headers, json=vm_config)
        if response.status_code == 200:
            print(f"VM {vm_name} modified in cluster {cluster_name}.")
        else:
            print(f"Failed to modify VM {vm_name} in cluster {cluster_name}: {response.text}")
