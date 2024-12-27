import os
import yaml
import requests
from .phpipam_manager import PhpIpamManager
from .vault_manager import VaultManager

class HarvesterManager:
    def __init__(self, site_config):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.clusters = self.load_clusters()
        self.profiles = self.load_profiles()
        self.phpipam_manager = PhpIpamManager(site_config)

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

    def load_profiles(self):
        profiles = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(self.config_path, filename), 'r') as f:
                        profile = yaml.safe_load(f)
                        profile_name = os.path.splitext(filename)[0]
                        profiles[profile_name] = profile
                except Exception as e:
                    print(f"Error loading profile {filename}: {str(e)}")
        return profiles

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

        api_url = self.site_config['harvester']['api_url']
        token = self.site_config['harvester']['api_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

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
                                "disks": [],
                                "interfaces": []
                            },
                            "resources": {
                                "requests": {
                                    "memory": f"{profile['memory']}Mi"
                                }
                            }
                        },
                        "volumes": [],
                        "networks": []
                    }
                }
            }
        }

        # Add disks
        for i, disk in enumerate(profile['disks']):
            disk_name = f"{payload['metadata']['name']}-disk-{i}"
            payload["spec"]["template"]["spec"]["domain"]["devices"]["disks"].append({
                "name": disk_name,
                "disk": {
                    "bus": "virtio"
                }
            })
            payload["spec"]["template"]["spec"]["volumes"].append({
                "name": disk_name,
                "persistentVolumeClaim": {
                    "claimName": disk_name
                }
            })

        # Add network interfaces
        for i, network in enumerate(profile['networks']):
            payload["spec"]["template"]["spec"]["domain"]["devices"]["interfaces"].append({
                "name": network['name'],
                "bridge": {}
            })
            payload["spec"]["template"]["spec"]["networks"].append({
                "name": network['name'],
                "multus": {
                    "networkName": network['name']
                }
            })

        try:
            response = requests.post(f"{api_url}/v1/harvester/kubevirt.io.virtualmachines", json=payload, headers=headers)
            response.raise_for_status()
            print(f"VM {payload['metadata']['name']} created successfully")
        except requests.exceptions.RequestException as e:
            print(f"Error creating VM: {str(e)}")

    def modify_vm(self, cluster_name, vm_name, profile_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        profile = self.profiles.get(profile_name)
        if not profile:
            print(f"Profile {profile_name} not found.")
            return

        api_url = self.site_config['harvester']['api_url']
        token = self.site_config['harvester']['api_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        try:
            # Retrieve the existing VM
            response = requests.get(f"{api_url}/v1/harvester/kubevirt.io.virtualmachines/{vm_name}", headers=headers)
            response.raise_for_status()
            vm = response.json()

            # Modify VM payload from profile
            vm['spec']['template']['spec']['domain']['cpu']['cores'] = profile['cpu']
            vm['spec']['template']['spec']['domain']['resources']['requests']['memory'] = f"{profile['memory']}Mi"
            vm['spec']['template']['spec']['domain']['devices']['disks'] = []
            vm['spec']['template']['spec']['volumes'] = []
            vm['spec']['template']['spec']['domain']['devices']['interfaces'] = []
            vm['spec']['template']['spec']['networks'] = []

            # Modify disks
            for i, disk in enumerate(profile['disks']):
                disk_name = f"{vm_name}-disk-{i}"
                vm['spec']['template']['spec']['domain']['devices']['disks'].append({
                    "name": disk_name,
                    "disk": {
                        "bus": "virtio"
                    }
                })
                vm['spec']['template']['spec']['volumes'].append({
                    "name": disk_name,
                    "persistentVolumeClaim": {
                        "claimName": disk_name
                    }
                })

            # Modify network interfaces
            for i, network in enumerate(profile['networks']):
                vm['spec']['template']['spec']['domain']['devices']['interfaces'].append({
                    "name": network['name'],
                    "bridge": {}
                })
                vm['spec']['template']['spec']['networks'].append({
                    "name": network['name'],
                    "multus": {
                        "networkName": network['name']
                    }
                })

            response = requests.put(f"{api_url}/v1/harvester/kubevirt.io.virtualmachines/{vm_name}", json=vm, headers=headers)
            response.raise_for_status()
            print(f"VM {vm_name} modified successfully")
        except requests.exceptions.RequestException as e:
            print(f"Error modifying VM: {str(e)}")

    def delete_vm(self, cluster_name, vm_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = self.site_config['harvester']['api_url']
        token = self.site_config['harvester']['api_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        try:
            response = requests.delete(f"{api_url}/v1/harvester/kubevirt.io.virtualmachines/{vm_name}", headers=headers)
            response.raise_for_status()
            print(f"VM {vm_name} deleted successfully")
        except requests.exceptions.RequestException as e:
            print(f"Error deleting VM: {str(e)}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = self.site_config['harvester']['api_url']
        token = self.site_config['harvester']['api_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        try:
            response = requests.get(f"{api_url}/v1/harvester/kubevirt.io.virtualmachines", headers=headers)
            response.raise_for_status()
            vms = response.json().get('items', [])
            for vm in vms:
                print(f"VM Name: {vm['metadata']['name']}, State: {vm['status']['phase']}")
        except requests.exceptions.RequestException as e:
            print(f"Error listing VMs: {str(e)}")
