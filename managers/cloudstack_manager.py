import os
import yaml
from cs import CloudStack

class CloudStackManager:
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
                    clusters[cluster_name] = CloudStack(endpoint=config['cloudstack_api_url'], key=config['cloudstack_api_key'], secret=config['cloudstack_api_secret'])
        return clusters

    def create_vm(self, cluster_name, profile):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            response = cluster.deployVirtualMachine(**profile)
            print(f"VM {response['name']} created in cluster {cluster_name}.")
        else:
            print(f"Cluster {cluster_name} not found.")

    def delete_vm(self, cluster_name, vm_id):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            cluster.destroyVirtualMachine(id=vm_id)
            print(f"VM {vm_id} deleted from cluster {cluster_name}.")
        else:
            print(f"Cluster {cluster_name} not found.")

    def list_vms(self, cluster_name):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            vms = cluster.listVirtualMachines()
            for vm in vms:
                print(f"VM ID: {vm['id']}, Name: {vm['name']}, State: {vm['state']}")
        else:
            print(f"Cluster {cluster_name} not found.")

    def modify_vm(self, cluster_name, vm_id, modifications):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            cluster.updateVirtualMachine(id=vm_id, **modifications)
            print(f"VM {vm_id} modified in cluster {cluster_name}.")
        else:
            print(f"Cluster {cluster_name} not found.")
