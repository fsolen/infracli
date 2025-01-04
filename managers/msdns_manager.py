import os
import yaml
import logging
from pywinrm import Session
from .vault_manager import VaultManager

class DNSManager:
    def __init__(self, site_config):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.dns_servers = self.load_dns_servers()
        self.logger = logging.getLogger(__name__)

    def load_dns_servers(self):
        dns_servers = {}
        config_path = os.path.join("configs", "dns_servers")
        if not os.path.exists(config_path):
            self.logger.error(f"DNS servers configuration directory not found: {config_path}")
            return dns_servers

        for filename in os.listdir(config_path):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(config_path, filename), 'r') as f:
                        config = yaml.safe_load(f)
                        domain = os.path.splitext(filename)[0]
                        dns_servers[domain] = config
                        self.logger.info(f"Loaded DNS server configuration for domain: {domain}")
                except Exception as e:
                    self.logger.error(f"Error loading DNS server configuration {filename}: {str(e)}")
        return dns_servers

    def get_dns_server(self, domain):
        return self.dns_servers.get(domain)

    def create_winrm_session(self, dns_server):
        try:
            username = self.credentials['username']
            password = self.credentials['password']
            session = Session(dns_server, auth=(username, password), transport='ntlm')
            return session
        except Exception as e:
            self.logger.error(f"Failed to create WinRM session to {dns_server}: {str(e)}")
            return None

    def run_winrm_command(self, command, dns_server):
        session = self.create_winrm_session(dns_server)
        if not session:
            return None

        try:
            result = session.run_ps(command)
            if result.status_code == 0:
                return result.std_out
            else:
                self.logger.error(f"WinRM command failed with status code {result.status_code}: {result.std_err}")
                return None
        except Exception as e:
            self.logger.error(f"Error executing WinRM command: {str(e)}")
            return None

    def check_if_exists(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        output = self.run_winrm_command(command, dns_server)
        return bool(output and output.strip())

    def get_dns_record(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        output = self.run_winrm_command(command, dns_server)
        if output:
            self.logger.info(f"DNS record for {name} ({record_type}):\n{output}")
        else:
            self.logger.warning(f"No DNS record found for {name} ({record_type})")

    def add_dns_record(self, record_type, name, value, ttl, dns_server, priority=None):
        if self.check_if_exists(record_type, name, dns_server):
            self.logger.warning(f"DNS record {name} ({record_type}) already exists.")
            return

        if record_type == 'A':
            command = f"Add-DnsServerResourceRecordA -ZoneName {dns_server} -Name {name} -IPv4Address {value} -TimeToLive {ttl}"
        elif record_type == 'CNAME':
            command = f"Add-DnsServerResourceRecordCName -ZoneName {dns_server} -Name {name} -HostNameAlias {value} -TimeToLive {ttl}"
        elif record_type == 'MX':
            if priority is None:
                self.logger.error("Priority is required for MX records.")
                return
            command = f"Add-DnsServerResourceRecordMX -ZoneName {dns_server} -Name {name} -MailExchange {value} -Preference {priority} -TimeToLive {ttl}"
        else:
            self.logger.error(f"Unsupported record type: {record_type}")
            return

        output = self.run_winrm_command(command, dns_server)
        if output:
            self.logger.info(f"DNS record {name} ({record_type}) added successfully.")
        else:
            self.logger.error(f"Failed to add DNS record {name} ({record_type}).")

    def del_dns_record(self, record_type, name, value, dns_server):
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RecordData {value} -RRType {record_type} -Force"
        output = self.run_winrm_command(command, dns_server)
        if output:
            self.logger.info(f"DNS record {name} ({record_type}) deleted successfully.")
        else:
            self.logger.error(f"Failed to delete DNS record {name} ({record_type}).")

    def list_dns_records(self, domain):
        dns_server = self.get_dns_server(domain)
        if not dns_server:
            self.logger.error(f"DNS server for domain {domain} not found.")
            return

        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server}"
        output = self.run_winrm_command(command, dns_server)
        if output:
            self.logger.info(f"DNS records for domain {domain}:\n{output}")
        else:
            self.logger.warning(f"No DNS records found for domain {domain}.")
