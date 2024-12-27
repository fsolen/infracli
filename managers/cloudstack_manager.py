import os
import yaml
from cs import CloudStack
from .phpipam_manager import PhpIpamManager
from .vault_manager import VaultManager

class CloudStackManager:
    def __init__(self, site_config, profiles_path):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.clusters = self.load_clusters()
        self.profiles_path = profiles_path  
        self.profiles = self.load_profiles()
        self.vm_count = {}  # Dictionary to keep track of VM counts for each cluster
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
        for filename in os.listdir(self.profiles_path): 
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(self.profiles_path, filename), 'r') as f:
                        profile = yaml.safe_load(f)
                        profile_name = os.path.splitext(filename)[0]
                        profiles[profile_name] = profile
                except Exception as e:
                    print(f"Error loading profile {filename}: {str(e)}")
        return profiles

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
        cluster = self.clusters.get(cluster_name)
        if not cluster:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        profile = self.profiles.get(profile_name)
        if not profile:
            print(f"Profile {profile_name} not found.")
            return

        api_url = self.site_config['cloudstack']['api_url']
        api_key = self.site_config['cloudstack']['api_key']
        secret_key = self.site_config['cloudstack']['secret_key']

        cloudstack = CloudStack(endpoint=api_url, key=api_key, secret=secret_key)

        try:
            network_info = self.allocate_ip(profile)
        except Exception as e:
            print(f"Error allocating IP: {str(e)}")
            return

        # Create VM payload from profile
        payload = {
            "serviceofferingid": profile['service_offering_id'],
            "templateid": profile['template_id'],
            "zoneid": profile['zone_id'],
            "networkids": profile['network_ids'],
            "name": profile['hostname_pattern'].format(index=1),
            "displayname": profile['hostname_pattern'].format(index=1),
            "ipaddress": network_info['ip_address'],
            "details": {
                "cpuNumber": profile['cpu'],
                "memory": profile['memory']
            }
        }

        # Add disks
        for i, disk in enumerate(profile['disks']):
            payload[f"disk{i+1}"] = {
                "size": disk['size_gb'] * 1024 * 1024,  # Convert GB to MB
                "name": disk['name']
            }

        # Add network interfaces
        for i, network in enumerate(profile['networks']):
            payload[f"nic{i+1}"] = {
                "networkid": network['network_id'],
                "name": network['name']
            }

        try:
            response = cloudstack.deployVirtualMachine(**payload)
            print(f"VM {response['name']} created successfully")
        except Exception as e:
            print(f"Error creating VM: {str(e)}")

    def modify_vm(self, cluster_name, vm_name, profile_name):
        cluster = self.clusters.get(cluster_name)
        if not cluster:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        profile = self.profiles.get(profile_name)
        if not profile:
            print(f"Profile {profile_name} not found.")
            return

        api_url = self.site_config['cloudstack']['api_url']
        api_key = self.site_config['cloudstack']['api_key']
        secret_key = self.site_config['cloudstack']['secret_key']

        cloudstack = CloudStack(endpoint=api_url, key=api_key, secret=secret_key)

        try:
            vm = self.get_vm_by_name(vm_name, cloudstack)
            if not vm:
                print(f"VM {vm_name} not found.")
                return

            # Modify VM payload from profile
            payload = {
                "id": vm['id'],
                "serviceofferingid": profile['service_offering_id'],
                "displayname": profile['hostname_pattern'].format(index=1),
                "details": {
                    "cpuNumber": profile['cpu'],
                    "memory": profile['memory']
                }
            }

            # Modify disks
            for i, disk in enumerate(profile['disks']):
                payload[f"disk{i+1}"] = {
                    "size": disk['size_gb'] * 1024 * 1024,  # Convert GB to MB
                    "name": disk['name']
                }

            # Modify network interfaces
            for i, network in enumerate(profile['networks']):
                payload[f"nic{i+1}"] = {
                    "networkid": network['network_id'],
                    "name": network['name']
                }

            response = cloudstack.updateVirtualMachine(**payload)
            print(f"VM {response['name']} modified successfully")
        except Exception as e:
            print(f"Error modifying VM: {str(e)}")

    def delete_vm(self, cluster_name, vm_name):
        cluster = self.clusters.get(cluster_name)
        if not cluster:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = self.site_config['cloudstack']['api_url']
        api_key = self.site_config['cloudstack']['api_key']
        secret_key = self.site_config['cloudstack']['secret_key']

        cloudstack = CloudStack(endpoint=api_url, key=api_key, secret=secret_key)

        try:
            vm = self.get_vm_by_name(vm_name, cloudstack)
            if not vm:
                print(f"VM {vm_name} not found.")
                return

            response = cloudstack.destroyVirtualMachine(id=vm['id'])
            print(f"VM {vm_name} deleted successfully")
        except Exception as e:
            print(f"Error deleting VM: {str(e)}")

    def list_vms(self, cluster_name):
        cluster = self.clusters.get(cluster_name)
        if not cluster:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = self.site_config['cloudstack']['api_url']
        api_key = self.site_config['cloudstack']['api_key']
        secret_key = self.site_config['cloudstack']['secret_key']

        cloudstack = CloudStack(endpoint=api_url, key=api_key, secret=secret_key)

        try:
            vms = cloudstack.listVirtualMachines()
            for vm in vms:
                print(f"VM Name: {vm['name']}, State: {vm['state']}")
        except Exception as e:
            print(f"Error listing VMs: {str(e)}")

    def get_vm_by_name(self, vm_name, cloudstack):
        try:
            vms = cloudstack.listVirtualMachines()
            for vm in vms:
                if vm['name'] == vm_name:
                    return vm
        except Exception as e:
            print(f"Error retrieving VM by name: {str(e)}")
        return None
