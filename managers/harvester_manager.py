import os
import yaml
from tabulate import tabulate
from kubevirt import KubeVirtClient
from .phpipam_manager import PhpIpamManager
from .vault_manager import VaultManager
from .vm_profile_manager import load_profiles


class HarvesterManager:
    def __init__(self, site_config, profiles_path):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.clusters = self.load_clusters()
        self.profiles_path = profiles_path
        self.profiles = load_profiles(self.profiles_path)
        self.phpipam_manager = PhpIpamManager(site_config)
        self.kubevirt_client = KubeVirtClient(api_url=self.site_config['harvester']['api_url'], token=self.site_config['harvester']['api_token'])

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

    def create_vm(self, cluster_name, profile_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        profile = self.profiles.get(profile_name)
        if not profile:
            print(f"Profile {profile_name} not found.")
            return

        try:
            network_info = self.phpipam_manager.allocate_ip(profile)
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
            self.kubevirt_client.create_virtual_machine(payload)
            print(f"VM {payload['metadata']['name']} created successfully")
        except Exception as e:
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

        try:
            # Retrieve the existing VM
            vm = self.kubevirt_client.get_virtual_machine(vm_name)

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

            self.kubevirt_client.update_virtual_machine(vm_name, vm)
            print(f"VM {vm_name} modified successfully")
        except Exception as e:
            print(f"Error modifying VM: {str(e)}")

    def delete_vm(self, cluster_name, vm_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        try:
            self.kubevirt_client.delete_virtual_machine(vm_name)
            print(f"VM {vm_name} deleted successfully")
        except Exception as e:
            print(f"Error deleting VM: {str(e)}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        try:
            vms = self.kubevirt_client.list_virtual_machines()
            vm_list = []
            for vm in vms:
                vm_list.append([
                    vm['metadata']['name'],
                    vm['spec']['template']['spec']['domain']['cpu']['cores'],
                    vm['spec']['template']['spec']['domain']['resources']['requests']['memory'],
                    len(vm['spec']['template']['spec']['domain']['devices']['disks']),
                    vm['status']['phase']
                ])
            print(tabulate(vm_list, headers=["VM Name", "vCPU", "Memory", "Disk Count", "State"], tablefmt="grid"))
        except Exception as e:
            print(f"Error listing VMs: {str(e)}")
