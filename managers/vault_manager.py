import hvac
import requests

class VaultManager:
    def __init__(self, site_config):
        self.site_config = site_config
        self.vault_hosts = self.site_config['vault'][0]['hosts']
        self.client = None
        self.token = None
        self.initialize_client()

    def initialize_client(self):
        for vault_host in self.vault_hosts:
            try:
                self.client = hvac.Client(url=f"http://{vault_host['host']}")
                self.token = self.get_vault_token(vault_host['base_url'])
                self.client.token = self.token
                break
            except Exception as e:
                print(f"Failed to connect to Vault host {vault_host['host']}: {str(e)}")
                continue
        if not self.client:
            raise Exception("Failed to connect to any Vault host")

    def get_vault_token(self, base_url):
        url = f"{base_url}/v1/auth/token/create"
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
