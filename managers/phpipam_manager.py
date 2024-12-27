import requests
import yaml
from .site_config import SiteConfig  # Import SiteConfig to load credentials

class PhpIpamManager:
    def __init__(self, site_name, config_path):
        self.site_config = SiteConfig(config_path).get_site_config(site_name)
        self.base_url = self.site_config['phpipam']['base_url']
        self.app_id = self.site_config['phpipam']['app_id']
        self.username = self.site_config['phpipam']['username']
        self.password = self.site_config['phpipam']['password']
        self.token = self.get_token()

    def get_token(self):
        url = f"{self.base_url}/api/{self.app_id}/user/"
        response = requests.post(url, auth=(self.username, self.password))
        response.raise_for_status()
        return response.json()['data']['token']

    def get_next_available_ip(self, vlan_name):
        subnet_id = self.get_subnet_id_by_vlan(vlan_name)
        url = f"{self.base_url}/api/{self.app_id}/subnets/{subnet_id}/first_free/"
        headers = {'token': self.token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def get_subnet_id_by_vlan(self, vlan_name):
        url = f"{self.base_url}/api/{self.app_id}/vlan/"
        headers = {'token': self.token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        vlans = response.json()['data']
        for vlan in vlans:
            if vlan['name'] == vlan_name:
                return vlan['subnetId']
        raise ValueError(f"VLAN {vlan_name} not found")

    def get_subnet_info(self, subnet_id):
        url = f"{self.base_url}/api/{self.app_id}/subnets/{subnet_id}/"
        headers = {'token': self.token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def get_network_info(self, vlan_name):
        subnet_id = self.get_subnet_id_by_vlan(vlan_name)
        ip_address = self.get_next_available_ip(vlan_name)
        subnet_info = self.get_subnet_info(subnet_id)
        network_info = {
            'ip_address': ip_address,
            'subnet_mask': subnet_info['mask'],
            'gateway': subnet_info['gateway'],
            'dns_servers': subnet_info['nameservers']
        }
        return network_info
