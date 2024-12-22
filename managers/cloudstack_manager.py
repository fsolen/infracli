import os
import yaml
from cs import CloudStack
from .phpipam_manager import PhpIpamManager

class CloudStackManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.clusters = self.load_clusters()
        self.profiles = self.load_profiles()
        self.vm_count = {}  # Dictionary to keep track of VM counts for each cluster
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

        api_url = cluster['api_url']
        api_key = cluster['api_key']
        secret_key = cluster['secret_key']

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
            "ipaddress": network_info['ip_address']
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

        api_url = cluster['api_url']
        api_key = cluster['api_key']
        secret_key = cluster['secret_key']

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
                "displayname": profile['hostname_pattern'].format(index=1)
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

        api_url = cluster['api_url']
        api_key = cluster['api_key']
        secret_key = cluster['secret_key']

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

        api_url = cluster['api_url']
        api_key = cluster['api_key']
        secret_key = cluster['secret_key']

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
