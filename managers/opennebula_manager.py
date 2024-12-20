import os
import yaml
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

    def get_server_proxy(self, cluster_name):
        config = self.get_cluster_config(cluster_name)
        if not config:
            print(f"Cluster configuration for {cluster_name} not found.")
            return None, None, None

        api_url = config['opennebula_api_url']
        username = config['opennebula_username']
        password = config['opennebula_password']
        server = ServerProxy(api_url)
        return server, username, password

    def validate_profile(self, profile):
        required_fields = ['hostname_pattern', 'template_name', 'cpu', 'memory', 'disks', 'ip_settings']
        for field in required_fields:
            if field not in profile:
                print(f"Profile validation failed: Missing required field '{field}'")
                return False

        if not isinstance(profile['disks'], list) or not all('name' in disk and 'size_gb' in disk for disk in profile['disks']):
            print("Profile validation failed: 'disks' must be a list of dictionaries with 'name' and 'size_gb' keys")
            return False

        ip_settings_fields = ['ip_address', 'subnet_mask', 'default_gateway', 'dns_servers']
        if not all(field in profile['ip_settings'] for field in ip_settings_fields):
            print(f"Profile validation failed: 'ip_settings' must contain {ip_settings_fields}")
            return False

        return True

    def create_vm(self, cluster_name, profile):
        if not self.validate_profile(profile):
            return

        server, username, password = self.get_server_proxy(cluster_name)
        if not server:
            return

        template_id = self.get_template_id(server, username, password, profile['template_name'])
        if not template_id:
            print(f"Template {profile['template_name']} not found in cluster {cluster_name}.")
            return

        vm_name = profile['hostname_pattern'].format(index=1)  # Example index, should be dynamically set
        vm_template = f"""
        NAME = "{vm_name}"
        CPU = "{profile['cpu']}"
        MEMORY = "{profile['memory']}"
        DISK = [
            {', '.join([f'NAME="{disk["name"]}", SIZE="{disk["size_gb"]}G"' for disk in profile['disks']])}
        ]
        NIC = [
            NETWORK = "{profile['vlan']}"
        ]
        CONTEXT = [
            HOSTNAME = "{vm_name}",
            IP = "{profile['ip_settings']['ip_address']}",
            NETMASK = "{profile['ip_settings']['subnet_mask']}",
            GATEWAY = "{profile['ip_settings']['default_gateway']}",
            DNS = "{', '.join(profile['ip_settings']['dns_servers'])}"
        ]
        """

        response = server.one.template.instantiate(username, password, template_id, vm_template, False, "")
        if response[0]:
            print(f"VM {vm_name} created in cluster {cluster_name}.")
        else:
            print(f"Failed to create VM in cluster {cluster_name}: {response[1]}")

    def get_template_id(self, server, username, password, template_name):
        response = server.one.templatepool.info(username, password, -2, -1, -1)
        if response[0]:
            templates = response[1].split('\n')
            for template in templates:
                if f'NAME="{template_name}"' in template:
                    return int(template.split()[1])
        return None

    def delete_vm(self, cluster_name, vm_id):
        server, username, password = self.get_server_proxy(cluster_name)
        if not server:
            return

        response = server.one.vm.action(username, password, 'terminate', vm_id)
        if response[0]:
            print(f"VM {vm_id} deleted from cluster {cluster_name}.")
        else:
            print(f"Failed to delete VM {vm_id} from cluster {cluster_name}: {response[1]}")

    def list_vms(self, cluster_name):
        server, username, password = self.get_server_proxy(cluster_name)
        if not server:
            return

        response = server.one.vmpool.info(username, password, -2, -1, -1, -1)
        if response[0]:
            vms = response[1].split('\n')
            for vm in vms:
                print(vm)
        else:
            print(f"Failed to list VMs in cluster {cluster_name}: {response[1]}")

    def modify_vm(self, cluster_name, vm_id, profile):
        if not self.validate_profile(profile):
            return

        server, username, password = self.get_server_proxy(cluster_name)
        if not server:
            return

        vm_template = f"""
        CPU = "{profile['cpu']}"
        MEMORY = "{profile['memory']}"
        DISK = [
            {', '.join([f'NAME="{disk["name"]}", SIZE="{disk["size_gb"]}G"' for disk in profile['disks']])}
        ]
        CONTEXT = [
            IP = "{profile['ip_settings']['ip_address']}",
            NETMASK = "{profile['ip_settings']['subnet_mask']}",
            GATEWAY = "{profile['ip_settings']['default_gateway']}",
            DNS = "{', '.join(profile['ip_settings']['dns_servers'])}"
        ]
        """

        response = server.one.vm.updateconf(username, password, vm_id, vm_template)
        if response[0]:
            print(f"VM {vm_id} modified in cluster {cluster_name}.")
        else:
            print(f"Failed to modify VM {vm_id} in cluster {cluster_name}: {response[1]}")
