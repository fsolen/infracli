import os
import yaml
import subprocess
from .vault_manager import VaultManager

class DNSManager:
    def __init__(self, site_config):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.dns_servers = self.load_dns_servers()

    def load_dns_servers(self):
        dns_servers = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    config = yaml.safe_load(f)
                    domain = os.path.splitext(filename)[0]
                    dns_servers[domain] = config
        return dns_servers

    def get_dns_server(self, domain):
        return self.dns_servers.get(domain)

    def run_winrm_command(self, command, dns_server):
        username = self.credentials['username']
        password = self.credentials['password']
        # Replace with actual implementation
        # session = winrm.Session(dns_server, auth=(username, password))
        # result = session.run_cmd(command)
        # return result.std_out
        print(f"Running command on {dns_server}: {command}")
        return subprocess.check_output(command, shell=True)

    def check_if_exists(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        try:
            output = self.run_winrm_command(command, dns_server)
            return bool(output.strip())
        except Exception as e:
            print(f"Error checking if record exists: {e}")
            return False

    def get_dns_record(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        try:
            output = self.run_winrm_command(command, dns_server)
            print(output.decode())
        except Exception as e:
            print(f"Error getting DNS record: {e}")

    def add_dns_record(self, record_type, name, value, ttl, dns_server, priority=None):
        command = f"Add-DnsServerResourceRecord{record_type} -ZoneName {dns_server} -Name {name} -IPv4Address {value} -TimeToLive {ttl}"
        if record_type == 'MX' and priority is not None:
            command += f" -Preference {priority}"
        try:
            self.run_winrm_command(command, dns_server)
            print(f"DNS record {name} added successfully.")
        except Exception as e:
            print(f"Error adding DNS record: {e}")

    def del_dns_record(self, record_type, name, value, dns_server):
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RecordData {value} -RRType {record_type} -Force"
        try:
            self.run_winrm_command(command, dns_server)
            print(f"DNS record {name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting DNS record: {e}")

    def list_dns_records(self, domain):
        dns_server = self.get_dns_server(domain)
        if not dns_server:
            print(f"DNS server for domain {domain} not found.")
            return

        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server}"
        try:
            output = self.run_winrm_command(command, dns_server)
            print(output.decode())
        except Exception as e:
            print(f"Error listing DNS records: {e}")
