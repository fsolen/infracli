import requests
import yaml

class PhpIpamManager:
    def __init__(self, config_path):
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)['phpipam']
        self.base_url = config['base_url']
        self.app_id = config['app_id']
        self.username = config['username']
        self.password = config['password']
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
