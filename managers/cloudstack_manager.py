import os
import yaml
from cs import CloudStack
from .phpipam_manager import PhpIpamManager

class CloudStackManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.clusters = self.load_clusters()
        self.vm_count = {}  # Dictionary to keep track of VM counts for each cluster
        self.phpipam_manager = PhpIpamManager(config_path)

    def load_clusters(self):
        clusters = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    config = yaml.safe_load(f)
                    cluster_name = os.path.splitext(filename)[0]
                    clusters[cluster_name] = CloudStack(endpoint=config['api_url'], key=config['api_key'], secret=config['secret_key'])
                    self.vm_count[cluster_name] = 0  # Initialize VM count for the cluster
        return clusters

    def allocate_ip(self, vm_profile):
        vlan_name = vm_profile.get('vlan')
        if vlan_name:
            ip_address = self.phpipam_manager.get_next_available_ip(vlan_name)
            return ip_address
        else:
            raise ValueError("VLAN not specified in vm_profile")

    def create_vm(self, cluster_name, profile):
        cluster = self.clusters.get(cluster_name)
        if cluster:
            self.vm_count[cluster_name] += 1  # Increment VM count for the cluster
            vm_index = self.vm_count[cluster_name]
            vm_name = profile['hostname_pattern'].format(index=vm_index)
            ip_address = self.allocate_ip(profile)
            vm_config = {
                'serviceofferingid': profile['service_offering'],
                'templateid': profile['template_name'],
                'zoneid': profile['zone'],
                'networkids': profile['network'],
                'name': vm_name,
                'displayname': vm_name,
                'cpu': profile['cpu'],
                'memory': profile['memory'],
                'disklist': [{'name': disk['name'], 'size': disk['size_gb']} for disk in profile['disks']],
                'ipaddress': ip_address,
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
