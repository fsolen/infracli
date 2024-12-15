import os
import yaml
import subprocess

class DNSManager:
    def __init__(self, config_path):
        self.config_path = config_path
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
        # Placeholder for running WinRM command
        # Replace with actual implementation
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
            print(output)
        except Exception as e:
            print(f"Error: {e}")

    def add_dns_record(self, record_type, name, value, ttl, dns_server, priority=None):
        if self.check_if_exists(record_type, name, dns_server):
            confirm = input(f"{record_type} record for {name} already exists. Do you want to update it? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Add operation cancelled.")
                return
            self.del_dns_record(record_type, name, value, dns_server, priority)

        if record_type == 'A':
            command = f"Add-DnsServerResourceRecordA -ZoneName {dns_server} -Name {name} -IPv4Address {value} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
            ptr_command = f"Add-DnsServerResourceRecordPtr -ZoneName {dns_server} -Name {value} -PtrDomainName {name} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
        elif record_type == 'CNAME':
            command = f"Add-DnsServerResourceRecordCName -ZoneName {dns_server} -Name {name} -HostNameAlias {value} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
        elif record_type == 'TXT':
            command = f"Add-DnsServerResourceRecordTxt -ZoneName {dns_server} -Name {name} -DescriptiveText '{value}' -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
        elif record_type == 'MX':
            command = f"Add-DnsServerResourceRecordMX -ZoneName {dns_server} -Name {name} -MailExchange {value} -Preference {priority} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
        else:
            print(f"Unsupported record type: {record_type}")
            return

        try:
            output = self.run_winrm_command(command, dns_server)
            print(output)
            if record_type == 'A':
                ptr_output = self.run_winrm_command(ptr_command, dns_server)
                print(ptr_output)
        except Exception as e:
            print(f"Error: {e}")

    def del_dns_record(self, record_type, name, value, dns_server, priority=None):
        if record_type == 'A':
            command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType A -RecordData {value} -Force"
            ptr_command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {value} -RRType PTR -RecordData {name} -Force"
        elif record_type == 'CNAME':
            command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType CNAME -RecordData {value} -Force"
        elif record_type == 'TXT':
            command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType TXT -RecordData '{value}' -Force"
        elif record_type == 'MX':
            command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType MX -RecordData {value} -Preference {priority} -Force"
        else:
            print(f"Unsupported record type: {record_type}")
            return

        try:
            output = self.run_winrm_command(command, dns_server)
            print(output)
            if record_type == 'A':
                ptr_output = self.run_winrm_command(ptr_command, dns_server)
                print(ptr_output)
        except Exception as e:
            print(f"Error: {e}")

    def list_dns_records(self, domain):
        dns_server = self.get_dns_server(domain)
        if not dns_server:
            print(f"DNS server not found for domain {domain}")
            return

        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server}"
        try:
            output = self.run_winrm_command(command, dns_server)
            print(output)
        except Exception as e:
            print(f"Error: {e}")
