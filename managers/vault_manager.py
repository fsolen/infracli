import hvac
import requests
from .site_config import SiteConfig

class VaultManager:
    def __init__(self, site_name, config_path):
        self.site_config = SiteConfig(config_path).get_site_config(site_name)
        self.vault_host = self.site_config['vault'][0]['host']
        self.vault_base_url = self.site_config['vault'][0]['base_url']
        self.client = hvac.Client(url=f"http://{self.vault_host}")
        self.client.token = self.get_vault_token()

    def get_vault_token(self):
        url = f"{self.vault_base_url}/v1/auth/token/create"
        payload = {
            "role": "your-role",
            "policies": ["default"]
        }
        headers = {
            "X-Vault-Token": "your-root-token"
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['auth']['client_token']

    def read_secret(self, path):
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data']
