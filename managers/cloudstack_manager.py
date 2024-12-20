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
                    clusters[cluster_name] = CloudStack(endpoint=config['api_url'], key=config['api_key'], secret=config['secret_key'])
        return clusters

    def create_vm(self, cluster_name, profile):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            vm_config = {
                'serviceofferingid': profile['service_offering'],
                'templateid': profile['template_name'],
                'zoneid': profile['zone'],
                'networkids': profile['network'],
                'name': profile['hostname_pattern'].format(index=1),  # Example index, should be dynamically set
                'displayname': profile['hostname_pattern'].format(index=1),
                'cpu': profile['cpu'],
                'memory': profile['memory'],
                'disklist': [{'name': disk['name'], 'size': disk['size_gb']} for disk in profile['disks']],
                'ipaddress': profile['ip_settings']['ip_address'],
                'netmask': profile['ip_settings']['subnet_mask'],
                'gateway': profile['ip_settings']['default_gateway'],
                'dns1': profile['ip_settings']['dns_servers'][0],
                'dns2': profile['ip_settings']['dns_servers'][1] if len(profile['ip_settings']['dns_servers']) > 1 else None
            }
            response = cluster.deployVirtualMachine(**vm_config)
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

    def modify_vm(self, cluster_name, vm_id, profile):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            cluster.updateVirtualMachine(id=vm_id, **profile)
            print(f"VM {vm_id} modified in cluster {cluster_name}.")
        else:
            print(f"Cluster {cluster_name} not found.")
