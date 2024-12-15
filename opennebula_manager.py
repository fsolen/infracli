import os
import yaml
import requests
from xmlrpc.client import ServerProxy

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
        username = config['opennebula_username']
        password = config['opennebula_password']
        server = ServerProxy(api_url)

        # Create VM payload from profile
        template = f"""
        NAME = "{profile['hostname_pattern'].format(index=1)}"
        CPU = "{profile['cpu']}"
        MEMORY = "{profile['memory']}"

        DISK = [
            IMAGE = "{profile['disks'][0]['name']}",
            SIZE = "{profile['disks'][0]['size_gb']}G"
        ]

        NIC = [
            NETWORK = "default"
        ]
        """

        try:
            response = server.one.template.instantiate(username + ":" + password, template, False, "", False)
            if response[0] == True:
                print(f"VM created successfully in cluster {cluster_name}.")
            else:
                print(f"Failed to create VM in cluster {cluster_name}: {response[1]}")
        except Exception as e:
            print(f"Error: {e}")

    def delete_vm(self, cluster_name, vm_id):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        username = config['opennebula_username']
        password = config['opennebula_password']
        server = ServerProxy(api_url)

        try:
            response = server.one.vm.action(username + ":" + password, "terminate", int(vm_id))
            if response[0] == True:
                print(f"VM {vm_id} deleted successfully from cluster {cluster_name}.")
            else:
                print(f"Failed to delete VM {vm_id} from cluster {cluster_name}: {response[1]}")
        except Exception as e:
            print(f"Error: {e}")

    def list_vms(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        username = config['opennebula_username']
        password = config['opennebula_password']
        server = ServerProxy(api_url)

        try:
            response = server.one.vmpool.info(username + ":" + password, -2, -1, -1, -1)
            if response[0] == True:
                vms = response[1]
                for vm in vms:
                    print(f"VM ID: {vm['ID']}, Name: {vm['NAME']}, Status: {vm['STATE']}")
            else:
                print(f"Failed to list VMs in cluster {cluster_name}: {response[1]}")
        except Exception as e:
            print(f"Error: {e}")

    def modify_vm(self, cluster_name, vm_id, profile):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return

        api_url = config['opennebula_api_url']
        username = config['opennebula_username']
        password = config['opennebula_password']
        server = ServerProxy(api_url)

        # Modify VM payload from profile
        template = f"""
        CPU = "{profile['cpu']}"
        MEMORY = "{profile['memory']}"

        DISK = [
            IMAGE = "{profile['disks'][0]['name']}",
            SIZE = "{profile['disks'][0]['size_gb']}G"
        ]

        NIC = [
            NETWORK = "default"
        ]
        """

        try:
            response = server.one.vm.update(username + ":" + password, int(vm_id), template, 1)
            if response[0] == True:
                print(f"VM {vm_id} modified successfully in cluster {cluster_name}.")
            else:
                print(f"Failed to modify VM {vm_id} in cluster {cluster_name}: {response[1]}")
        except Exception as e:
            print(f"Error: {e}")
